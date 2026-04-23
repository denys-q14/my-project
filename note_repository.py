from sqlalchemy.orm import Session
from models import Note, Reminder
from sqlalchemy.exc import SQLAlchemyError

class NoteRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_active_notes(self, user_id: int):
        """
        Повертає всі неархівовані нотатки користувача.
        """
        return self.session.query(Note).filter_by(user_id=user_id, is_archived=False).all()

    def create_with_reminder(self, note_data: dict, reminder_data: dict):
        """
        Створює нотатку та нагадування в одній транзакції.
        Якщо створення Reminder впаде, Note теж не створиться.
        """
        try:
            with self.session.begin():
                note = Note(**note_data)
                self.session.add(note)
                self.session.flush()  # отримати note.id
                reminder = Reminder(note_id=note.id, **reminder_data)
                self.session.add(reminder)
            return note, reminder
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
