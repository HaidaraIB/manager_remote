from sqlalchemy import (
    Column,
    Integer,
    select,
    insert,
    delete,
)
from models.DB import (
    Base,
    connect_and_close,
    lock_and_release,
)
from sqlalchemy.orm import Session


class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True)

    @staticmethod
    @connect_and_close
    def check_admin(user_id: int, s: Session = None):
        res = s.execute(select(Admin).where(Admin.id == user_id))
        try:
            return res.fetchone().t[0]
        except:
            pass

    @staticmethod
    @connect_and_close
    def get_admin_ids(s: Session = None):
        res = s.execute(select(Admin))
        try:
            return list(map(lambda x: x[0], res.tuples().all()))
        except:
            pass

    @staticmethod
    @lock_and_release
    async def add_new_admin(admin_id: int, s: Session = None):
        s.execute(insert(Admin).values(id=admin_id).prefix_with("OR IGNORE"))

    @staticmethod
    @lock_and_release
    async def remove_admin(admin_id: int, s: Session = None):
        s.execute(delete(Admin).where(Admin.id == admin_id))
