from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from config import DATABASE_URL


class Base(DeclarativeBase):
    pass



connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else{}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    
    import models 
    Base.metadata.create_all(bind=engine)
