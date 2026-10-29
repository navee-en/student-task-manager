from app import app, db, User
from werkzeug.security import generate_password_hash
from getpass import getpass

with app.app_context():

    username = "admin"
    email = "admin@taskmanager.local"
    password = getpass("Enter a new admin password: ")
    existing_admin = User.query.filter_by(role="Admin").first()

    if existing_admin:
        print("Admin account already exists.")
    else:

        existing_username = User.query.filter_by(
            username=username
        ).first()

        if existing_username:
            print("Username 'admin' already exists.")
        else:

            existing_email = User.query.filter_by(
                email=email
            ).first()

            if existing_email:
                print("Email already exists.")
            else:

                admin = User(
                    username=username,
                    email=email,
                    password=generate_password_hash(password),
                    role="Admin",
                    department="Administration",
                    course="System Administration"
                )

                db.session.add(admin)
                db.session.commit()

                print("Admin account created successfully.")