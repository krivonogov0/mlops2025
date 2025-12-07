import asyncio
import httpx
import numpy as np
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from .logger import MonitoringLogger
from .config import Config

TEST_IMAGE_URL = "https://storage.googleapis.com/sfr-vision-language-research/BLIP/demo.jpg"


class ServiceMonitor:
    def __init__(self, config: Config, logger: MonitoringLogger):
        self.config = config
        self.logger = logger
        self.base_url = config.service.base_url
        self.consecutive_failures = 0
        self.last_alert_time: Optional[datetime] = None
        self.latency_history: List[float] = []

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=self.config.monitoring.request_timeout_seconds) as client:
                response = await client.get(f"{self.base_url}/health")
                healthy = response.status_code == 200
                if not healthy:
                    self.logger.log("WARNING", f"Health check failed: {response.status_code}")
                return healthy

        except Exception as e:
            self.logger.log("ERROR", f"Health check error: {e}")
            return False

    async def send_test_image(self) -> Dict[str, Any]:
        """Отправить демо-изображение на /predict."""
        try:
            # Скачиваем изображение
            async with httpx.AsyncClient() as client:
                img_resp = await client.get(TEST_IMAGE_URL, timeout=10)
                img_resp.raise_for_status()
                image_bytes = img_resp.content

            start_time = time.time()
            async with httpx.AsyncClient(timeout=self.config.monitoring.request_timeout_seconds) as client:
                files = {"file": ("demo.jpg", image_bytes, "image/jpeg")}
                response = await client.post(f"{self.base_url}/predict", files=files)
            elapsed = (time.time() - start_time) * 1000  # ms

            success = response.status_code == 200
            if success:
                result = response.json()
                caption = result.get("result", {}).get("prediction", "N/A")
                self.logger.log("INFO", f"✅ Prediction OK: '{caption}' | {elapsed:.1f} ms")
            else:
                self.logger.log("ERROR", f"❌ Prediction failed: {response.status_code} – {response.text}")

            return {
                "success": success,
                "latency_ms": elapsed,
                "status_code": response.status_code,
            }

        except Exception as e:
            elapsed = (time.time() - start_time) * 1000 if 'start_time' in locals() else -1  # type: ignore
            self.logger.log("ERROR", f"❌ Prediction exception: {e}")
            return {
                "success": False,
                "latency_ms": elapsed,
                "error": str(e),
                "status_code": None,
            }

    def calculate_p95(self, latencies: List[float]) -> float:
        if not latencies:
            return 0.0
        return float(np.percentile([x for x in latencies if x > 0], 95))

    def determine_alert_level(self, metrics: Dict[str, Any]) -> str:
        t = self.config.thresholds

        # Response time
        avg_resp = metrics.get("avg_response_time_ms", 0)
        if avg_resp > t.response_time_ms["critical"]:
            return "red"
        elif avg_resp > t.response_time_ms["warning"]:
            return "yellow"

        # P95
        p95 = metrics.get("p95_latency_ms", 0)
        if p95 > t.p95_latency_ms["critical"]:
            return "red"
        elif p95 > t.p95_latency_ms["warning"]:
            return "yellow"

        # Error rate
        err_rate = metrics.get("error_rate_percent", 0)
        if err_rate > t.error_rate_percent["critical"]:
            return "red"
        elif err_rate > t.error_rate_percent["warning"]:
            return "yellow"

        # Consecutive failures
        cons = self.consecutive_failures
        if cons >= t.consecutive_failures["critical"]:
            return "red"
        elif cons >= t.consecutive_failures["warning"]:
            return "yellow"

        return "green"

    def should_alert(self) -> bool:
        if not self.config.alerts.enabled:
            return False
        if self.last_alert_time is None:
            return True
        cooldown_sec = self.config.alerts.cooldown_minutes * 60
        return (datetime.now() - self.last_alert_time).total_seconds() >= cooldown_sec

    async def run_check_cycle(self):
        """Выполнить цикл мониторинга."""
        self.logger.log("INFO", "🔍 Starting monitoring cycle...")

        # 1. Health check
        healthy = await self.health_check()
        if not healthy:
            self.consecutive_failures += 1
        else:
            self.consecutive_failures = 0

        # 2. Check /predict
        results = []
        for _ in range(self.config.monitoring.samples_per_check):
            res = await self.send_test_image()
            results.append(res)
            if res["success"]:
                self.latency_history.append(res["latency_ms"])
            await asyncio.sleep(0.5)

        # 3. Metrics
        latencies = [r["latency_ms"] for r in results if r["success"] and r["latency_ms"] > 0]
        total = len(results)
        failed = len([r for r in results if not r["success"]])
        error_rate = (failed / total * 100) if total > 0 else 0
        avg_latency = np.mean(latencies) if latencies else 0

        # Update history
        self.latency_history = self.latency_history[-100:]

        p95 = self.calculate_p95(self.latency_history)

        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "health_status": healthy,
            "consecutive_failures": self.consecutive_failures,
            "total_requests": total,
            "failed_requests": failed,
            "error_rate_percent": round(error_rate, 2),
            "avg_response_time_ms": round(float(avg_latency), 2),
            "p95_latency_ms": round(p95, 2),
            "sample_latencies_ms": latencies,
        }

        self.logger.log_metrics(metrics)

        # 4. Check alert level
        level = self.determine_alert_level(metrics)

        if level != "green" and self.should_alert():
            self.last_alert_time = datetime.now()
            self.logger.alert(level, f"Service degraded! Error rate: {error_rate:.1f}%, P95: {p95:.1f} ms")

        self.logger.log("INFO", f"📊 Cycle complete | Errors: {failed}/{total} | Avg: {avg_latency:.1f} ms | P95: {p95:.1f} ms")

    async def start_monitoring(self):
        """Запустить цикл мониторинга."""
        self.logger.log("INFO", "🚀 Monitoring started!")
        while True:
            try:
                await self.run_check_cycle()
                await asyncio.sleep(self.config.monitoring.check_interval_seconds)
            except KeyboardInterrupt:
                self.logger.log("INFO", "🛑 Monitoring stopped by user")
                break
            except Exception as e:
                self.logger.log("ERROR", f"Unexpected error in monitoring loop: {e}")
                await asyncio.sleep(5)
