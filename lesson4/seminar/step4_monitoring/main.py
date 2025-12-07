import asyncio
from src.config import load_config
from src.logger import MonitoringLogger
from src.monitor import ServiceMonitor

def main():
    config = load_config("config/monitoring_config.yaml")
    logger = MonitoringLogger(
        log_file=config.logging.log_file,
        metrics_file=config.logging.metrics_file,
        console_colors=config.logging.console_colors,
    )
    monitor = ServiceMonitor(config, logger)

    try:
        asyncio.run(monitor.start_monitoring())
    except KeyboardInterrupt:
        logger.log("INFO", "Monitoring terminated.")

if __name__ == "__main__":
    main()
