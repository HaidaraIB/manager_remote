from telegram import Update, InlineKeyboardMarkup
from common.common import build_accounts_keyboard
from common.back_to_home_page import back_to_user_home_page_button


async def reply_with_user_accounts(update: Update):
    keybaord = [
        build_accounts_keyboard(user_id=update.effective_user.id),
        back_to_user_home_page_button[0],
    ]
    await update.callback_query.edit_message_text(
        text="اختر حساباً من حساباتك المسجلة لدينا",
        reply_markup=InlineKeyboardMarkup(keybaord),
    )
