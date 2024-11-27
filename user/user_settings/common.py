from telegram import InlineKeyboardButton

def build_user_settings_keyboard():
    return [
        [
            InlineKeyboardButton(
                text="الحسابات البنكية",
                callback_data="bank_accounts_settings"
            )
        ]
    ]