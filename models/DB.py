from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, Session
import traceback
from asyncio import Lock
from models import *
from common.constants import *
from common.error_handler import write_error, read_error

lock = Lock()
Base = declarative_base()
# engine = create_engine("sqlite:///data_test/test.sqlite3")
engine = create_engine("sqlite:///data/database.sqlite3")


def create_tables():
    Base.metadata.create_all(engine)


def lock_and_release(func):
    async def wrapper(*args, **kwargs):
        try:
            await lock.acquire()
            s = Session(bind=engine, autoflush=True)
            result = await func(*args, **kwargs, s=s)
            s.commit()
            if result:
                return result
        except Exception as e:
            print(e)
            if not read_error(str(e)):
                write_error(traceback.format_exc() + "\n\n")
        finally:
            s.close()
            lock.release()

    return wrapper


def connect_and_close(func):
    def wrapper(*args, **kwargs):
        s = Session(bind=engine, autoflush=True)
        result = func(*args, **kwargs, s=s)
        s.close()
        return result

    return wrapper
