from telegram.ext import (
    ContextTypes,
)

from DB import DB

import user.make_complaint as mkc

async def make_complaint_data(
    context: ContextTypes.DEFAULT_TYPE,
    callback_data: list,
):
    try:
        data = context.user_data["complaint_data"]
    except KeyError:
        complaint = DB.get_complaint(
            order_serial=int(callback_data[-1]), order_type=callback_data[-2]
        )
        order = DB.get_one_order(
            serial=int(callback_data[-1]), order_type=callback_data[-2]
        )
        data = {
            "text": (
                f"شكوى جديدة:\n\n"
                f"{mkc.stringify_order(serial=int(callback_data[-1]), order_type=callback_data[-2])}\n\n"
                "سبب الشكوى:\n"
                f"<b>{complaint['reason']}</b>\n\n"
            ),
            "media": (
                await mkc.get_photos_from_archive(
                    message_ids=[
                        m_id for m_id in map(int, order['archive_message_ids'].split(","))
                    ]
                )
            ),
        }
        context.user_data["complaint_data"] = data
    return data