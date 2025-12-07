from pathlib import Path
from pydantic import BaseModel, Field
import yaml


class ThresholdsConfig(BaseModel):
    response_time_ms: dict = Field(..., example={"warning": 2000, "critical": 5000})
    p95_latency_ms: dict
    error_rate_percent: dict
    consecutive_failures: dict


class AlertsConfig(BaseModel):
    enabled: bool
    cooldown_minutes: int


class LoggingConfig(BaseModel):
    console_colors: bool
    log_file: str
    metrics_file: str


class MonitoringConfig(BaseModel):
    check_interval_seconds: int
    samples_per_check: int
    request_timeout_seconds: int


class ServiceConfig(BaseModel):
    host: str
    port: int
    base_url: str


class Config(BaseModel):
    service: ServiceConfig
    monitoring: MonitoringConfig
    thresholds: ThresholdsConfig
    alerts: AlertsConfig
    logging: LoggingConfig


def load_config(config_path: str = "config/monitoring_config.yaml") -> Config:
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return Config(**data)
