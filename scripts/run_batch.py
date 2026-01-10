import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.services.scheduler_service import process_scheduled_tasks


def main():
    db = SessionLocal()
    try:
        process_scheduled_tasks(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()

