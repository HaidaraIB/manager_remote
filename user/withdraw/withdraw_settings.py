from telegram import Chat, Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, ConversationHandler
from user.withdraw.common import build_withdraw_settings_keyboard
from common.back_to_home_page import back_to_user_home_page_button
from common.decorators import (
    check_if_user_present_decorator,
    check_if_user_created_account_from_bot_decorator,
)
from common.force_join import check_if_user_member_decorator


@check_if_user_present_decorator
@check_if_user_member_decorator
@check_if_user_created_account_from_bot_decorator
async def withdraw_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        keyboard = build_withdraw_settings_keyboard()
        keyboard.append(back_to_user_home_page_button[0])
        await update.callback_query.edit_message_text(
            text="إعدادات السحب",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return ConversationHandler.END


back_to_withdraw_settings = withdraw_settings

withdraw_settings_handler = CallbackQueryHandler(
    withdraw_settings, "^withdraw_settings$"
)

back_to_withdraw_settings_handler = CallbackQueryHandler(
    back_to_withdraw_settings, "^back_to_withdraw_settings$"
)
