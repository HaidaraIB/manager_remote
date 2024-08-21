from sqlalchemy import select, insert, delete, and_
from sqlalchemy.orm import Session
from models.BaseUser import BaseUser
from models.DB import lock_and_release, connect_and_close


class Worker(BaseUser):
    __abstract__ = True

    @classmethod
    @lock_and_release
    async def add_worker(
        cls,
        worker_id: int,
        name: str,
        username: str,
        method: str = None,
        check_what: str = None,
        is_point: bool = False,
        s: Session = None,
    ):
        values = {"id": worker_id, "name": name, "username": username}

        if check_what:
            values.update({"check_what": check_what})
        if method:
            values.update({"method": method})
        if is_point:
            values.update({"is_point": is_point})

        res = s.execute(insert(cls).values(values).prefix_with("OR IGNORE"))
        return res.lastrowid

    @classmethod
    @connect_and_close
    def get_workers(
        cls,
        worker_id: int = None,
        s: Session = None,
    ):
        if worker_id:
            res = s.execute(
                select(cls).where(cls.id == worker_id)
            )  # get list of workers by id
        else:
            res = s.execute(select(cls))  # get all agents
        try:
            return list(map(lambda x: x[0], res.tuples().all()))
        except:
            pass

    @classmethod
    @lock_and_release
    async def remove_worker(
        cls,
        worker_id: int,
        method: str = None,
        check_what: str = None,
        is_point: bool = None,
        s: Session = None,
    ):
        if is_point:
            s.execute(
                delete(cls).where(
                    and_(
                        cls.id == worker_id,
                        cls.is_point == is_point,
                    )
                )
            )
        elif check_what: # if check_what is not None then method is not None too.
            s.execute(
                delete(cls).where(
                    and_(
                        cls.id == worker_id,
                        cls.check_what == check_what,
                        cls.method == method,
                    )
                )
            )
        elif method:
            s.execute(
                delete(cls).where(and_(cls.id == worker_id, cls.method == method))
            )
