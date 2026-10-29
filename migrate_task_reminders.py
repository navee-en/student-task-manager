from sqlalchemy import inspect, text
from app import app, db

with app.app_context():
    inspector = inspect(db.engine)

    columns = {
        column["name"]
        for column in inspector.get_columns("task")
    }

    with db.engine.begin() as connection:
        if "reminder_day_before_sent" not in columns:
            connection.execute(text("""
                ALTER TABLE task
                ADD COLUMN reminder_day_before_sent
                BOOLEAN NOT NULL DEFAULT 0
            """))

        if "reminder_due_date_sent" not in columns:
            connection.execute(text("""
                ALTER TABLE task
                ADD COLUMN reminder_due_date_sent
                BOOLEAN NOT NULL DEFAULT 0
            """))

    print("Task reminder database migration completed.")