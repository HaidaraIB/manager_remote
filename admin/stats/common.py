from telegram import InlineKeyboardButton


def build_stats_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(
                text="الإيداعات 📥",
                callback_data="deposit_stats",
            ),
        ],
        [
            InlineKeyboardButton(
                text="السحوبات 💳",
                callback_data="withdraw_stats",
            ),
        ],
        [
            InlineKeyboardButton(
                text="المحافظ 👝",
                callback_data="wallets_stats",
            ),
        ],
    ]
    return keyboard