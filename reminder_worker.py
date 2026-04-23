from fastapi import BackgroundTasks
from sqlalchemy import create_engine, select, and_
from sqlalchemy.orm import Session
from models import Reminder
from datetime import datetime
import time

DATABASE_URL = "sqlite:///test.db"  # замініть на свій URL для PostgreSQL
engine = create_engine(DATABASE_URL)

# Додаємо поле status до Reminder для прикладу (у реальній БД має бути)

def check_reminders():
    with Session(engine) as session:
        now = datetime.now()
        reminders = session.execute(
            select(Reminder).where(
                and_(Reminder.remind_at <= now, Reminder.status == 'pending')
            )
        ).scalars().all()
        for reminder in reminders:
            print(f"Нагадування {reminder.id} спрацювало!")
            # Тут можна змінити статус або виконати дію

# Для FastAPI
from fastapi import FastAPI
app = FastAPI()

def periodic_check():
    while True:
        check_reminders()
        time.sleep(60)

@app.on_event("startup")
def start_worker():
    import threading
    thread = threading.Thread(target=periodic_check, daemon=True)
    thread.start()
