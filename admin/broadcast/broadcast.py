from telegram import Chat, Update, InlineKeyboardMarkup, error
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from admin.broadcast.common import send_to, build_done_button, build_broadcast_keyboard
from common.common import build_admin_keyboard
from common.back_to_home_page import (
    back_to_admin_home_page_handler,
    back_to_admin_home_page_button,
)
from start import admin_command, start_command
from custom_filters import Admin
import models
import asyncio

(
    THE_MESSAGE,
    SEND_TO,
    ENTER_USERS,
) = range(3)


async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        await update.callback_query.edit_message_text(
            text=(
                "أرسل الرسالة.\n"
                "يمكنك إرسال نص أو ملف وسائط أو الاثنين معاً.\n"
                "ملاحظة: إرسال مجموعة ملفات وسائط غير متاح حالياً."
            ),
            reply_markup=InlineKeyboardMarkup(back_to_admin_home_page_button),
        )
        return THE_MESSAGE


async def get_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        if update.message:
            context.user_data["the message"] = update.message
            await update.message.reply_text(
                text="هل تريد إرسال الرسالة إلى:",
                reply_markup=build_broadcast_keyboard(),
            )
        else:
            await update.callback_query.edit_message_text(
                text="هل تريد إرسال الرسالة إلى:",
                reply_markup=build_broadcast_keyboard(),
            )

        return SEND_TO


back_to_the_message = broadcast_message


async def choose_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        if update.callback_query.data == "specific users":
            context.user_data["specific users"] = set()
            await update.callback_query.edit_message_text(
                text="قم بإرسال آيديات المستخدمين الذين تريد إرسال الرسالة لهم عند الانتهاء اضغط تم الانتهاء.",
                reply_markup=build_done_button(),
            )
            return ENTER_USERS

        if update.callback_query.data == "all users":
            all_users = set(map(lambda x: x.id, models.User.get_all_users()))
            asyncio.create_task(send_to(user_ids=all_users, context=context))

        elif update.callback_query.data == "agents":
            asyncio.create_task(
                send_to(
                    user_ids=models.WorkWithUsOrder.get_user_ids(role="agent"),
                    context=context,
                )
            )
        keyboard = build_admin_keyboard()
        await update.callback_query.edit_message_text(
            text="يقوم البوت بإرسال الرسائل الآن، يمكنك متابعة استخدامه بشكل طبيعي.",
            reply_markup=keyboard,
        )

        return ConversationHandler.END


back_to_send_to = get_message


async def enter_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        user_id = int(update.message.text)
        punch_line = "تابع مع باقي الآيديات واضغط تم الانتهاء عند الانتهاء."

        try:
            await context.bot.get_chat(chat_id=user_id)
        except error.TelegramError:
            await update.message.reply_text(
                text=(
                    "لم يتم العثور على المستخدم، ربما لم يبدأ محادثة مع البوت بعد ❗️\n"
                    + punch_line
                ),
                reply_markup=build_done_button(),
            )
            return

        context.user_data["specific users"].add(user_id)
        await update.message.reply_text(
            text="تم العثور على المستخدم ✅\n" + punch_line,
            reply_markup=build_done_button(),
        )
        return ENTER_USERS


async def done_entering_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        keyboard = build_admin_keyboard()
        await update.callback_query.edit_message_text(
            text="يقوم البوت بإرسال الرسائل الآن، يمكنك متابعة استخدامه بشكل طبيعي.",
            reply_markup=keyboard,
        )
        asyncio.create_task(
            send_to(
                user_ids=context.user_data["specific users"],
                context=context,
            )
        )
        return ConversationHandler.END


broadcast_message_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            broadcast_message,
            "^broadcast$",
        )
    ],
    states={
        THE_MESSAGE: [
            MessageHandler(
                filters=(filters.TEXT & ~filters.COMMAND)
                | filters.PHOTO
                | filters.CAPTION
                | filters.VIDEO,
                callback=get_message,
            )
        ],
        SEND_TO: [
            CallbackQueryHandler(
                callback=choose_target,
                pattern="^((all)|(specific)) users$|^agents$",
            )
        ],
        ENTER_USERS: [
            CallbackQueryHandler(
                done_entering_users,
                "^done entering users$",
            ),
            MessageHandler(
                filters=filters.Regex("^\d+$"),
                callback=enter_users,
            ),
        ],
    },
    fallbacks=[
        CallbackQueryHandler(
            back_to_send_to,
            "^back_to_send_to$",
        ),
        CallbackQueryHandler(
            back_to_the_message,
            "^back_to_the_message$",
        ),
        back_to_admin_home_page_handler,
        admin_command,
        start_command,
    ],
)
