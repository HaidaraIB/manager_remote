from sqlalchemy import Column, Integer, String, TIMESTAMP, Text, Float, func, insert
from sqlalchemy.orm import Session
from database.BaseOrder import BaseOrder
from database.DB import lock_and_release
from telegram import PhotoSize
import datetime


class TrustedAgentsOrder(BaseOrder):
    __tablename__ = "trusted_agents_orders"

    serial = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer)
    gov = Column(String)
    neighborhood = Column(Text)
    latitude = Column(Text)
    longitude = Column(Text)
    email = Column(Text)
    phone = Column(Text)
    state = Column(String, default="pending")
    reason = Column(Text)

    # Front sign details
    front_id = Column(Text)
    front_unique_id = Column(Text)
    front_width = Column(Text)
    front_height = Column(Text)
    front_size = Column(Text)

    # Back sign details
    back_id = Column(Text)
    back_unique_id = Column(Text)
    back_width = Column(Text)
    back_height = Column(Text)
    back_size = Column(Text)

    amount = Column(Float)
    ref_number = Column(Text)
    creation_date = Column(TIMESTAMP, server_default=func.current_timestamp())
    approve_date = Column(TIMESTAMP)
    decline_date = Column(TIMESTAMP)

    @staticmethod
    @lock_and_release
    async def decline_trusted_agent_order(serial: int, reason: str, s: Session = None):
        s.query(TrustedAgentsOrder).filter_by(serial=serial).update(
            {
                TrustedAgentsOrder.decline_date: datetime.datetime.now(),
                TrustedAgentsOrder.state: "decline",
                TrustedAgentsOrder.reason: reason,
            }
        )

    @staticmethod
    @lock_and_release
    async def add_trusted_agent_order(
        user_id: int,
        gov: str,
        neighborhood: str,
        latitude: str,
        longitude: str,
        email:str,
        phone:str,
        amount:float,
        front_id: PhotoSize,
        back_id: PhotoSize,
        ref_num: str,
        s: Session = None,
    ):
        res = s.execute(
            insert(TrustedAgentsOrder).values(
                user_id=user_id,
                gov=gov,
                neighborhood=neighborhood,
                latitude=latitude,
                longitude=longitude,
                email=email,
                phone=phone,
                amount=amount,
                front_id=front_id.file_id,
                front_unique_id=front_id.file_unique_id,
                front_size=front_id.file_size,
                front_width=front_id.width,
                front_height=front_id.height,
                back_id=back_id.file_id,
                back_unique_id=back_id.file_unique_id,
                back_size=back_id.file_size,
                back_width=back_id.width,
                back_height=back_id.height,
                ref_number=ref_num,
            )
        )
        return res.lastrowid
