from sqlalchemy import Column, String, PrimaryKeyConstraint
from models.Worker import Worker


class Checker(Worker):
    __tablename__ = "checkers"
    check_what = Column(String)
    method = Column(String)
    __table_args__ = (
        PrimaryKeyConstraint("id", "check_what", "method", name="_id_check_what_method_uc"),
    )