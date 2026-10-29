
from sqlalchemy import text
from app import app, db

new_columns = {
    "registration_number": "VARCHAR(50)",
    "semester": "VARCHAR(20)",
    "academic_year": "VARCHAR(20)",
    "faculty_id": "VARCHAR(50)",
    "qualification": "VARCHAR(150)",
    "designation": "VARCHAR(100)",
    "profile_image_key": "VARCHAR(500)",
}

with app.app_context():
    existing_columns = {
        column["name"]
        for column in db.inspect(db.engine).get_columns("user")
    }

    with db.engine.begin() as connection:
        for column_name, column_type in new_columns.items():
            if column_name not in existing_columns:
                connection.execute(text(
                    f"ALTER TABLE user ADD COLUMN "
                    f"{column_name} {column_type}"
                ))
                print(f"Added: {column_name}")

        connection.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS "
            "uq_user_registration_number "
            "ON user (registration_number)"
        ))

        connection.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS "
            "uq_user_faculty_id "
            "ON user (faculty_id)"
        ))

    print("Profile database migration completed.")
