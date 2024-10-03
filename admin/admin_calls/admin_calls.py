from telegram import (
    Chat,
    Update,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
    ReplyKeyboardMarkup,
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from common.back_to_home_page import (
    back_to_admin_home_page_button,
    back_to_admin_home_page_handler,
)
from common.common import build_admin_keyboard, request_buttons
from start import admin_command, start_command
from custom_filters import Admin
from admin.admin_calls.common import build_turn_user_calls_on_or_off_keyboard
from common.constants import *


USER_CALL_TO_TURN_ON_OR_OFF = 0


async def find_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        if update.effective_message.users_shared:
            await update.message.reply_text(
                text=f"🆔: <code>{update.effective_message.users_shared.users[0].user_id}</code>",
            )
        else:
            await update.message.reply_text(
                text=f"🆔: <code>{update.effective_message.chat_shared.chat_id}</code>",
            )


async def hide_ids_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        if (
            not context.user_data.get("request_keyboard_hidden", None)
            or not context.user_data["request_keyboard_hidden"]
        ):
            context.user_data["request_keyboard_hidden"] = True
            await update.callback_query.delete_message()
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text="تم الإخفاء✅",
                reply_markup=ReplyKeyboardRemove(),
            )
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text=HOME_PAGE_TEXT,
                reply_markup=build_admin_keyboard(),
            )
        else:
            context.user_data["request_keyboard_hidden"] = False

            await update.callback_query.delete_message()
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text="تم الإظهار✅",
                reply_markup=ReplyKeyboardMarkup(request_buttons, resize_keyboard=True),
            )
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text=HOME_PAGE_TEXT,
                reply_markup=build_admin_keyboard(),
            )


async def turn_user_calls_on_or_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        if not update.callback_query.data == "turn user calls on or off":
            data = update.callback_query.data.replace("on_off ", "")
            if context.bot_data["user_calls"].get(data, True):
                context.bot_data["user_calls"][data] = False
                await update.callback_query.answer(
                    text="تم إيقاف الزر 🔴",
                    show_alert=True,
                )
            else:
                context.bot_data["user_calls"][data] = True
                await update.callback_query.answer(
                    text="تم تشغيل الزر 🟢",
                    show_alert=True,
                )

        keyboard = build_turn_user_calls_on_or_off_keyboard(context=context)
        keyboard.append(back_to_admin_home_page_button[0])
        await update.callback_query.edit_message_text(
            text="اختر الزر🔘",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return USER_CALL_TO_TURN_ON_OR_OFF


turn_user_calls_on_or_off_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            turn_user_calls_on_or_off,
            "^turn user calls on or off$",
        )
    ],
    states={
        USER_CALL_TO_TURN_ON_OR_OFF: [
            CallbackQueryHandler(
                turn_user_calls_on_or_off,
                "^on_off",
            )
        ]
    },
    fallbacks=[
        back_to_admin_home_page_handler,
        admin_command,
        start_command,
    ],
)


hide_ids_keyboard_handler = CallbackQueryHandler(
    callback=hide_ids_keyboard, pattern="^hide ids keyboard$"
)

find_id_handler = MessageHandler(
    filters=filters.StatusUpdate.USER_SHARED | filters.StatusUpdate.CHAT_SHARED,
    callback=find_id,
)
