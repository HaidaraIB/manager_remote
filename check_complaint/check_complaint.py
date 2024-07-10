from telegram.ext import (
    ContextTypes,
)

from DB import DB

from user.make_complaint.make_complaint import stringify_order, get_photos_from_archive


async def make_complaint_data(
    context: ContextTypes.DEFAULT_TYPE,
    callback_data: list,
):
    complaint = DB.get_complaint(
        order_serial=int(callback_data[-1]), order_type=callback_data[-2]
    )
    try:
        data = context.user_data[f"complaint_data_{complaint['id']}"]
    except KeyError:
        order = DB.get_one_order(
            serial=int(callback_data[-1]), order_type=callback_data[-2]
        )
        data = {
            "text": (
                f"شكوى جديدة:\n\n"
                f"{stringify_order(serial=int(callback_data[-1]), order_type=callback_data[-2])}\n\n"
                "سبب الشكوى:\n"
                f"<b>{complaint['reason']}</b>\n\n"
            ),
            "media": (
                await get_photos_from_archive(
                    message_ids=[
                        m_id
                        for m_id in map(int, order["archive_message_ids"].split(","))
                    ]
                )
            ),
        }
        context.user_data[f"complaint_data_{complaint['id']}"] = data
    return data
