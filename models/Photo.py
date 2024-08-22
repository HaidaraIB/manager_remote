from sqlalchemy import Column, String, Integer, select, insert, and_
from sqlalchemy.orm import Session
from models.DB import Base, connect_and_close, lock_and_release
from telegram import InputMediaPhoto, PhotoSize


class Photo(Base):
    __tablename__ = "photos"
    file_id = Column(String, primary_key=True)
    file_unique_id = Column(String)
    width = Column(Integer)
    height = Column(Integer)
    file_size = Column(Integer)
    order_serial = Column(Integer)
    order_type = Column(String)

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
        s.execute(insert(Photo).values(values).prefix_with("OR IGNORE"))

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
