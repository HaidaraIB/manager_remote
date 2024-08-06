from sqlalchemy import Column, Integer, select, insert, and_
from sqlalchemy.orm import Session
from models.DB import connect_and_close, lock_and_release
from models.BaseMedia import BaseMedia
from telegram import PhotoSize


class Photo(BaseMedia):
    __tablename__ = "photos"
    width = Column(Integer)
    height = Column(Integer)

    @staticmethod
    @lock_and_release
    async def add(
        photos: list[PhotoSize],
        order_serial: int,
        order_type: str,
        s: Session = None,
    ):
        values = []
        for p in photos:
            p_dict = {
                "file_id": p.file_id,
                "file_unique_id": p.file_unique_id,
                "width": p.width,
                "height": p.height,
                "file_size": p.file_size,
                "order_serial": order_serial,
                "order_type": order_type,
            }
            values.append(p_dict)
        s.execute(insert(Photo).values(values))

    @staticmethod
    @connect_and_close
    def get(
        order_serial: int,
        order_type: str,
        s: Session = None,
    ):
        res = s.execute(
            select(Photo).where(
                and_(
                    Photo.order_serial == order_serial,
                    Photo.order_type == order_type,
                )
            )
        )
        try:
            return [
                PhotoSize(
                    file_id=p.file_id,
                    file_unique_id=p.file_unique_id,
                    width=p.width,
                    height=p.height,
                    file_size=p.file_size,
                )
                for p in list(map(lambda x: x[0], res.tuples().fetchall()))
            ]
        except:
            pass
