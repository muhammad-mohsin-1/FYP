"""Central config loader: config/settings.yaml + FYP_ env overrides.

Keeps every tunable in one documented place instead of scattered
literals. Environment variables win over the YAML file.
"""
import os

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
YAML_PATH = os.path.join(BASE_DIR, "config", "settings.yaml")

_defaults = {
    "app": {"name": "Contraband Detection API", "host": "0.0.0.0", "port": 8000},
    "model": {"path": "ai/runs/best.pt", "default_confidence": 0.50,
              "frame_skip_default": 3},
    "storage": {"database_url": "sqlite:///./fyp.db",
                "upload_dir": "backend/uploads",
                "evidence_dir": "evidence",
                "report_dir": "reports"},
    "auth": {"jwt_secret": "change-me-in-production",
             "jwt_expire_minutes": 480},
    "seed": {"admin_username": "admin", "admin_password": "admin123",
             "zones": []},
}

_cfg = {k: dict(v) for k, v in _defaults.items()}
if yaml and os.path.exists(YAML_PATH):
    with open(YAML_PATH) as f:
        for section, values in (yaml.safe_load(f) or {}).items():
            if isinstance(values, dict) and section in _cfg:
                _cfg[section].update(values)


def get(section: str, key: str, env: str | None = None):
    """Read a config value; env vars override the YAML file.

    Checks FYP_<ENV> first, then the legacy bare <ENV> name
    (e.g. MODEL_PATH, DATABASE_URL) for backwards compatibility.
    """
    if env:
        for name in (f"FYP_{env}", env):
            if os.environ.get(name):
                return os.environ[name]
    return _cfg.get(section, {}).get(key, _defaults[section][key])


MODEL_PATH = get("model", "path", "MODEL_PATH")
DEFAULT_CONF = float(get("model", "default_confidence", "DEFAULT_CONF"))
FRAME_SKIP_DEFAULT = int(get("model", "frame_skip_default", "FRAME_SKIP"))
DATABASE_URL = get("storage", "database_url", "DATABASE_URL")
UPLOAD_DIR = get("storage", "upload_dir", "UPLOAD_DIR")
EVIDENCE_DIR = get("storage", "evidence_dir", "EVIDENCE_DIR")
REPORT_DIR = get("storage", "report_dir", "REPORT_DIR")
JWT_SECRET = get("auth", "jwt_secret", "JWT_SECRET")
JWT_EXPIRE_MIN = int(get("auth", "jwt_expire_minutes", "JWT_EXPIRE_MIN"))
