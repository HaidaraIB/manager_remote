from sqlalchemy import select, insert, and_
from sqlalchemy.orm import Session
from models.DB import connect_and_close, lock_and_release
from models.BaseMedia import BaseMedia
from telegram import Document


class Doc(BaseMedia):
    __tablename__ = "docs"

    @lock_and_release
    async def add(
        docs: list[Document],
        order_serial: int,
        order_type: str,
        s: Session = None,
    ):
        values = []
        for p in docs:
            p_dict = {
                "file_id": p.file_id,
                "file_unique_id": p.file_unique_id,
                "file_size": p.file_size,
                "order_serial": order_serial,
                "order_type": order_type,
            }
            values.append(p_dict)
        s.execute(insert(Doc).values(values))

    @staticmethod
    @connect_and_close
    def get(
        order_serial: int,
        order_type: str,
        s: Session = None,
    ):
        res = s.execute(
            select(Doc).where(
                and_(
                    Doc.order_serial == order_serial,
                    Doc.order_type == order_type,
                )
            )
        )
        try:
            return [
                Document(
                    file_id=p.file_id,
                    file_unique_id=p.file_unique_id,
                    file_size=p.file_size,
                )
                for p in list(map(lambda x: x[0], res.tuples().fetchall()))
            ]
        except:
            pass
