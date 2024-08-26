from telegram import InlineKeyboardButton
from common.common import build_back_button
from common.back_to_home_page import back_to_user_home_page_button

complaints_keyboard = [
    [InlineKeyboardButton(text="إيداع📥", callback_data="deposit complaint")],
    [InlineKeyboardButton(text="سحب💳", callback_data="withdraw complaint")],
    [
        InlineKeyboardButton(
            text="شراء USDT💰",
            callback_data="busdt complaint",
        )
    ],
    back_to_user_home_page_button[0],
]


def build_orders_keyboard(serials: list[int]):
    keyboard = []
    for i in range(0, len(serials), 3):
        row = []
        row.append(
            InlineKeyboardButton(
                text=str(serials[i]), callback_data=f"serial {serials[i]}"
            )
        )
        if i + 1 < len(serials):
            row.append(
                InlineKeyboardButton(
                    text=str(serials[i + 1]), callback_data=f"serial {serials[i+1]}"
                )
            )
        if i + 1 < len(serials) - 1:
            row.append(
                InlineKeyboardButton(
                    text=str(serials[i + 2]), callback_data=f"serial {serials[i+2]}"
                )
            )
        keyboard.append(row)

    keyboard.append(build_back_button("back_to_choose_order_type"))
    keyboard.append(back_to_user_home_page_button[0])
    return keyboard
