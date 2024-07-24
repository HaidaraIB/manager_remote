from telegram import (
    Chat,
    Update,
    InlineKeyboardButton,
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
    build_admin_keyboard,
    build_back_button,
)

from common.back_to_home_page import (
    back_to_admin_home_page_handler,
    back_to_admin_home_page_button,
)

from start import admin_command, start_command
from models import User, TrustedAgentsOrder
import asyncio
from custom_filters import Admin

(
    THE_MESSAGE,
    SEND_TO,
    ENTER_USERS,
) = range(3)


async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        await update.callback_query.edit_message_text(
            text="أرسل الرسالة.",
            reply_markup=InlineKeyboardMarkup(back_to_admin_home_page_button),
        )
        return THE_MESSAGE


async def the_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        admin_settings_keyboard = [
            [
                InlineKeyboardButton(
                    text="جميع المستخدمين👥", callback_data="all users"
                ),
                InlineKeyboardButton(
                    text="مستخدمين محددين👤", callback_data="specific users"
                ),
                InlineKeyboardButton(text="الوكلاء", callback_data="agents"),
            ],
            build_back_button("back_to_the_message"),
            back_to_admin_home_page_button[0],
        ]
        if update.message:
            context.user_data["the message"] = update.message.text
            await update.message.reply_text(
                text="هل تريد إرسال الرسالة إلى:",
                reply_markup=InlineKeyboardMarkup(admin_settings_keyboard),
            )
        else:
            await update.callback_query.edit_message_text(
                text="هل تريد إرسال الرسالة إلى:",
                reply_markup=InlineKeyboardMarkup(admin_settings_keyboard),
            )

        return SEND_TO


back_to_the_message = broadcast_message


async def send_to_all(context: ContextTypes.DEFAULT_TYPE):
    all_users = User.get_all_users()
    text = context.user_data["the message"]
    for user in all_users:
        try:
            await context.bot.send_message(chat_id=user.id, text=text)
        except:
            pass


async def send_to_some(users: list, context: ContextTypes.DEFAULT_TYPE):
    text = context.user_data["the message"]
    for user in users:
        try:
            await context.bot.send_message(chat_id=user, text=text)
        except:
            pass


async def send_to(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        if update.callback_query.data == "specific users":
            context.user_data["specific users"] = []
            done_button = [
                [
                    InlineKeyboardButton(
                        text="تم الانتهاء👍", callback_data="done entering users"
                    )
                ],
                build_back_button("back_to_send_to"),
                back_to_admin_home_page_button[0],
            ]
            await update.callback_query.edit_message_text(
                text="قم بإرسال آيديات المستخدمين الذين تريد إرسال الرسالة لهم عند الانتهاء اضغط تم الانتهاء.",
                reply_markup=InlineKeyboardMarkup(done_button),
            )
            return ENTER_USERS
        
        if update.callback_query.data == "all users":
            asyncio.create_task(send_to_all(context=context))

        elif update.callback_query.data == "agents":
            asyncio.create_task(
                send_to_some(users=TrustedAgentsOrder.get_user_ids(), context=context)
            )
        keyboard = build_admin_keyboard()
        await update.callback_query.edit_message_text(
            text="يقوم البوت بإرسال الرسائل الآن، يمكنك متابعة استخدامه بشكل طبيعي.",
            reply_markup=keyboard,
        )

        return ConversationHandler.END


back_to_send_to = the_message


async def enter_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        if update.message.text.isnumeric():
            context.user_data["specific users"].append(int(update.message.text))
        else:
            await update.message.reply_text(text="الرجاء إرسال id.")


async def done_entering_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        keyboard = build_admin_keyboard()
        await update.callback_query.edit_message_text(
            text="يقوم البوت بإرسال الرسائل الآن، يمكنك متابعة استخدامه بشكل طبيعي.",
            reply_markup=keyboard,
        )
        asyncio.create_task(
            send_to_some(users=context.user_data["specific users"], context=context)
        )
        return ConversationHandler.END


broadcast_message_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(broadcast_message, "^broadcast$")],
    states={
        THE_MESSAGE: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND, callback=the_message
            )
        ],
        SEND_TO: [
            CallbackQueryHandler(
                callback=send_to, pattern="^((all)|(specific))users$|^agents$"
            )
        ],
        ENTER_USERS: [
            CallbackQueryHandler(done_entering_users, "^done entering users$"),
            MessageHandler(filters=filters.Regex("^\d+$"), callback=enter_users),
        ],
    },
    fallbacks=[
        CallbackQueryHandler(back_to_send_to, "^back_to_send_to$"),
        CallbackQueryHandler(back_to_the_message, "^back_to_the_message$"),
        back_to_admin_home_page_handler,
        admin_command,
        start_command,
    ],
)
