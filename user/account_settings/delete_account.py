from telegram import Update, Chat, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler
from common.back_to_home_page import (
    back_to_user_home_page_button,
    back_to_user_home_page_handler,
)
from common.decorators import (
    check_if_user_created_account_from_bot_decorator,
    check_if_user_present_decorator,
)
from common.common import build_confirmation_keyboard, build_back_button
from user.account_settings.common import reply_with_user_accounts
from common.force_join import check_if_user_member_decorator
import models
from start import start_command


ACCOUNT, CONFIRM_DELETE_ACCOUNT = range(2)


@check_if_user_present_decorator
@check_if_user_member_decorator
@check_if_user_created_account_from_bot_decorator
async def delete_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        await reply_with_user_accounts(update)
        return ACCOUNT


async def choose_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        if not update.callback_query.data.startswith("back"):
            acc_num = update.callback_query.data
            context.user_data["acc_num_to_del"] = acc_num
        else:
            acc_num = context.user_data["acc_num_to_del"]
        confirmation_keyboard = [
            build_confirmation_keyboard("delete_account"),
            build_back_button("back_to_choose_account"),
            back_to_user_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text=f"هل أنت متأكد من أنك تريد حذف الحساب صاحب الرقم: <b>{acc_num}</b>",
            reply_markup=InlineKeyboardMarkup(confirmation_keyboard),
        )
        return CONFIRM_DELETE_ACCOUNT


back_to_choose_account = delete_account


async def confirm_delete_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        if update.callback_query.data.startswith("yes"):
            await models.Account.delete_account(
                acc_num=context.user_data["acc_num_to_del"]
            )
            await update.callback_query.answer(
                "تم حذف الحساب بنجاح ✅", show_alert=True
            )
        await reply_with_user_accounts(update)
        return ACCOUNT


delete_account_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            delete_account,
            "^delete account$",
        )
    ],
    states={
        ACCOUNT: [
            CallbackQueryHandler(
                choose_account,
                "^\d+$",
            )
        ],
        CONFIRM_DELETE_ACCOUNT: [
            CallbackQueryHandler(
                confirm_delete_account,
                "^((yes)|(no))_delete_account$",
            )
        ],
    },
    fallbacks=[
        start_command,
        back_to_user_home_page_handler,
        CallbackQueryHandler(back_to_choose_account, "^back_to_choose_account$"),
    ],
    name="delete_account_conversation",
    persistent=True,
)
