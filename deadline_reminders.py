from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app import app, db, Task, User, send_email


def check_deadline_reminders():
    today = datetime.now(ZoneInfo("Asia/Kolkata")).date()
    tomorrow = today + timedelta(days=1)

    with app.app_context():
        tasks = Task.query.filter(
            Task.due_date.in_([today, tomorrow]),
            Task.status != "Completed",
            Task.student_id.isnot(None)
        ).all()

        for task in tasks:
            student = User.query.filter_by(
                id=task.student_id,
                role="Student"
            ).first()

            if not student:
                continue

            # Reminder one day before the deadline
            if (
                task.due_date == tomorrow
                and not task.reminder_day_before_sent
            ):
                sent = send_email(
                    student.email,
                    f"Deadline tomorrow: {task.title}",
                    f"""Hello {student.username},

This is a reminder that your task is due tomorrow.

Task: {task.title}
Subject: {task.subject or "Not specified"}
Deadline: {task.due_date.strftime("%d %B %Y")}
Status: {task.status}

Please log in to your Student Task Management System
and complete the task before the deadline.
"""
                )

                if sent:
                    task.reminder_day_before_sent = True
                    db.session.commit()

            # Reminder on the deadline date
            if (
                task.due_date == today
                and not task.reminder_due_date_sent
            ):
                sent = send_email(
                    student.email,
                    f"Task deadline today: {task.title}",
                    f"""Hello {student.username},

Your task deadline is today.

Task: {task.title}
Subject: {task.subject or "Not specified"}
Deadline: {task.due_date.strftime("%d %B %Y")}
Status: {task.status}

Please review your task and complete it as soon as possible.
"""
                )

                if sent:
                    task.reminder_due_date_sent = True
                    db.session.commit()

        print(f"Deadline reminder check completed for {today}.")


if __name__ == "__main__":
    check_deadline_reminders()