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
        s: Session = None,
    ):
        values = {"id": worker_id, "name": name, "username": username}

        if check_what:
            values.update({"check_what": check_what})
        elif method:
            values.update({"method": method})

        s.execute(insert(cls).values(values).prefix_with("OR IGNORE"))

    @classmethod
    @connect_and_close
    def get_workers(
        cls,
        worker_id: int = None,
        method: str = None,
        check_what: str = None,
        deposit: str = None,
        s: Session = None,
    ):
        if worker_id:
            if method:
                res = s.execute(
                    select(cls).where(and_(cls.id == worker_id, cls.method == method))
                )  # get payment agent
            elif check_what:
                res = s.execute(
                    select(cls).where(
                        and_(cls.id == worker_id, cls.check_what == check_what)
                    )
                )  # get checker
            elif deposit:
                res = s.execute(
                    select(cls).where(cls.id == worker_id)
                )  # get deposit agent
            else:
                res = s.execute(
                    select(cls).where(cls.id == worker_id)
                )  # get list of workers by id

            if method or check_what or deposit:
                try:
                    return res.fetchone().t[0]
                except:
                    pass

        elif method:
            res = s.execute(
                select(cls).where(cls.method == method)
            )  # get all payment agents with same method
        elif check_what:
            res = s.execute(
                select(cls).where(cls.check_what == check_what)
            )  # get all checker with same role
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
        s: Session = None,
    ):
        delete_cond = True
        if method:
            delete_cond = cls.method == method
        elif check_what:
            delete_cond = cls.check_what == check_what

        s.execute(delete(cls).where(and_(cls.id == worker_id, delete_cond)))
