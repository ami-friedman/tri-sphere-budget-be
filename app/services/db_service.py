from sqlmodel import Session


def add_to_db(session: Session, db_obj):
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj
