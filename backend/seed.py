"""Seed script: creates the default admin user and starter zones.

Run once after first startup:
    python -m backend.seed        (from the project root, venv active)

Default admin: username=admin / password=admin123
Change the password immediately after first login.
"""
from .database import SessionLocal, init_db
from .models import User, Zone, Setting
from .auth import hash_password
from . import app_config

DEFAULT_ZONES = [
    ("Server Room", "Restricted IT infrastructure area - no phones, no smoking"),
    ("Petrol Pump", "Fuel station forecourt - strict no-smoking zone"),
    ("Examination Hall", "University exam venue - no mobile phones allowed"),
]


def main():
    init_db()
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == "admin").first():
            db.add(User(username="admin",
                        password_hash=hash_password("admin123"),
                        role="admin"))
            print("created admin user (admin / admin123)")
        for name, desc in DEFAULT_ZONES:
            if not db.query(Zone).filter(Zone.name == name).first():
                db.add(Zone(name=name, description=desc))
                print(f"created zone: {name}")
        if not db.query(Setting).filter(Setting.key == "conf_threshold").first():
            db.add(Setting(key="conf_threshold",
                           value=str(app_config.DEFAULT_CONF)))
            print(f"created default confidence threshold: {app_config.DEFAULT_CONF}")
        db.commit()
        print("seed complete")
    finally:
        db.close()


if __name__ == "__main__":
    main()
