from sqlalchemy import Column, String, PrimaryKeyConstraint, select, and_
from models.Worker import Worker
from sqlalchemy.orm import Session
from models.DB import connect_and_close


class Checker(Worker):
    __tablename__ = "checkers"
    check_what = Column(String)
    method = Column(String)
    __table_args__ = (
        PrimaryKeyConstraint(
            "id", "check_what", "method", name="_id_check_what_method_uc"
        ),
    )

    @classmethod
    @connect_and_close
    def get_workers(
        cls,
        worker_id: int = None,
        method: str = None,
        check_what: str = None,
        s: Session = None,
    ):
        if worker_id and check_what and method:
            res = s.execute(
                select(cls).where(
                    and_(
                        cls.id == worker_id,
                        cls.check_what == check_what,
                        cls.method == method,
                    )
                )
            )  # get checker
            try:
                return res.fetchone().t[0]
            except:
                pass
        elif worker_id and check_what:
            res = s.execute(
                select(cls).where(
                    and_(
                        cls.id == worker_id,
                        cls.check_what == check_what,
                    )
                )
            )  # get all roles for checker
        elif check_what and method:
            res = s.execute(
                select(cls).where(
                    and_(
                        cls.check_what == check_what,
                        cls.method == method,
                    )
                )
            )  # get all checker with same role
        elif worker_id:
            return super().get_workers(worker_id=worker_id)
        else:
            return super().get_workers()
        
        try:
            return list(map(lambda x: x[0], res.tuples().all()))
        except:
            pass
