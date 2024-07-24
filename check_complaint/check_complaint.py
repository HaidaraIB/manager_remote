from telegram.ext import (
    ContextTypes,
)

from models import Complaint, Photo
from user.make_complaint.make_complaint import stringify_order
from common.common import parent_to_child_models_mapper


async def make_complaint_data(
    context: ContextTypes.DEFAULT_TYPE,
    callback_data: list[str],
):
    order_type = callback_data[-2]
    order_serial = int(callback_data[-1])
    complaint = Complaint.get_complaint(
        order_serial=order_serial,
        order_type=order_type,
    )
    try:
        data = context.user_data[f"complaint_data_{complaint.id}"]
    except KeyError:
        order = parent_to_child_models_mapper[order_type].get_one_order(
            serial=order_serial
        )
        data = {
            "text": (
                f"شكوى جديدة:\n\n"
                f"{stringify_order(serial=order_serial, order_type=order_type)}\n\n"
                "سبب الشكوى:\n"
                f"<b>{complaint.reason}</b>\n\n"
            ),
            "media": (
                await Photo.get(
                    order_serial=order_serial,
                    order_type=order_type.replace("busdt", "buy_usdt"),
                )
            ),
        }
        context.user_data[f"complaint_data_{complaint.id}"] = data
    return data
