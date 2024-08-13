from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def build_check_deposit_keyboard(serial: int):
    keyboard = [
        [
            InlineKeyboardButton(
                text="تعديل المبلغ", callback_data=f"edit_deposit_amount_{serial}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="إرسال الطلب ⬅️", callback_data=f"send_deposit_order_{serial}"
            ),
            InlineKeyboardButton(
                text="رفض الطلب ❌", callback_data=f"decline_deposit_order_{serial}"
            ),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)
