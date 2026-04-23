from models import Base, User, Note, Reminder
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

engine = create_engine('sqlite:///test.db')
Base.metadata.create_all(engine)

with Session(engine) as session:
    # Users
    users = [
        User(name=f"User{i}", email=f"user{i}@example.com")
        for i in range(1, 6)
    ]
    session.add_all(users)
    session.flush()  # assign ids

    # Notes
    notes = [
        Note(
            user_id=users[i % 5].id,
            title=f"Note {i+1}",
            content=f"Content for note {i+1}",
            is_archived=(i % 2 == 0),
            created_at=datetime.utcnow() - timedelta(days=i)
        )
        for i in range(5)
    ]
    session.add_all(notes)
    session.flush()

    # Reminders
    reminders = [
        Reminder(
            note_id=notes[i].id,
            remind_at=datetime.utcnow() + timedelta(days=i)
        )
        for i in range(5)
    ]
    session.add_all(reminders)
    session.commit()
print("5 записів у кожній таблиці створено.")
