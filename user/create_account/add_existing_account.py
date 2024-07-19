from telegram import (
    Update,
    Chat,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from common.common import (
    build_user_keyboard,
    build_back_button,
)
from common.decorators import check_if_user_present_decorator

from common.back_to_home_page import (
    back_to_user_home_page_button,
    back_to_user_home_page_handler,
)

from start import start_command

from common.force_join import check_if_user_member_decorator

from models import Account
(GET_FULL_NAME, GET_ACC_NUM, GET_PASSWORD) = range(3)


@check_if_user_present_decorator
@check_if_user_member_decorator
async def add_existing_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        await update.callback_query.edit_message_text(
            text="قم بإرسال رقم الحساب",
            reply_markup=InlineKeyboardMarkup(back_to_user_home_page_button),
        )
        return GET_ACC_NUM


async def get_acc_num(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:

        back_buttons = [
            build_back_button("back_to_get_acc_num"),
            back_to_user_home_page_button[0],
        ]

        if update.callback_query:
            await update.callback_query.edit_message_text(
                text="قم بإرسال الاسم الثلاثي",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
            return GET_FULL_NAME

        account = Account.get_account(acc_num=update.message.text)
        if not account:
            await update.message.reply_text(
                text="هذا الحساب غير منشأ عن طريق البوت!",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
            return

        context.user_data["acc_num"] = update.message.text
        await update.message.reply_text(
            text="قم بإرسال الاسم الثلاثي",
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return GET_FULL_NAME


back_to_get_acc_num = add_existing_account


async def get_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        back_buttons = [
            build_back_button("back_to_get_full_name"),
            back_to_user_home_page_button[0],
        ]
        if update.message:
            context.user_data["full_name"] = update.message.text
            await update.message.reply_text(
                text="قم بإرسال كلمة المرور",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        else:
            await update.callback_query.edit_message_text(
                text="قم بإرسال كلمة المرور",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )

        return GET_PASSWORD


back_to_get_full_name = get_acc_num


async def get_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        await Account.connect_account_to_user(
            user_id=update.effective_user.id,
            acc_num=context.user_data["acc_num"],
        )
        await update.message.reply_text(
            text="تمت إضافة الحساب بنجاح ✅", reply_markup=build_user_keyboard()
        )
        return ConversationHandler.END


add_existing_account_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(add_existing_account, "^add existing account$")],
    states={
        GET_ACC_NUM: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=get_acc_num,
            )
        ],
        GET_FULL_NAME: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=get_full_name,
            )
        ],
        GET_PASSWORD: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=get_password,
            )
        ],
    },
    fallbacks=[
        CallbackQueryHandler(back_to_get_acc_num, "^back_to_get_acc_num$"),
        CallbackQueryHandler(back_to_get_full_name, "^back_to_get_full_name$"),
        back_to_user_home_page_handler,
        start_command,
    ],
)
