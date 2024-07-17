from telegram import (
    Chat,
    Update,
    InlineKeyboardButton,
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

from common.common import (
    build_admin_keyboard,
    build_methods_keyboard,
    payment_method_pattern,
    request_buttons,
)

from common.back_to_home_page import back_to_admin_home_page_button

from common.back_to_home_page import back_to_admin_home_page_handler

from start import admin_command

from DB import DB
from custom_filters.Admin import Admin


(
    PAYMENT_METHOD_TO_TURN_ON_OR_OFF,
    USER_CALL_TO_TURN_ON_OR_OFF,
) = range(2)

turn_user_calls_on_or_off_keyboard = [
    [InlineKeyboardButton(text="سحب💳", callback_data="awithdraw")],
    [InlineKeyboardButton(text="إيداع™️", callback_data="adeposit")],
    [InlineKeyboardButton(text="إنشاء حساب موثق™️", callback_data="acreate account")],
    [InlineKeyboardButton(text="شراء USDT", callback_data="abuy usdt")],
    [InlineKeyboardButton(text="إنشاء شكوى🗳", callback_data="amake complaint")],
    back_to_admin_home_page_button[0],
]


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
                text="القائمة الرئيسية🔝",
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
                text="القائمة الرئيسية🔝",
                reply_markup=build_admin_keyboard(),
            )


async def turn_payment_method_on_or_off(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        payment_methods_keyboard = build_methods_keyboard()
        payment_methods_keyboard.append(back_to_admin_home_page_button[0])
        await update.callback_query.edit_message_text(
            text="اختر وسيلة الدفع💳.",
            reply_markup=InlineKeyboardMarkup(payment_methods_keyboard),
        )
        return PAYMENT_METHOD_TO_TURN_ON_OR_OFF


async def payment_method_to_turn_on_or_off(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        method = DB.get_payment_method(name=update.callback_query.data)
        if method[1]:
            await DB.turn_payment_method_on_or_off(name=update.callback_query.data)
            await update.callback_query.answer("تم إيقاف وسيلة الدفع✅")
        else:
            await DB.turn_payment_method_on_or_off(
                name=update.callback_query.data, on=True
            )
            await update.callback_query.answer("تم تشغيل وسيلة الدفع✅")

        payment_methods_keyboard = build_methods_keyboard()
        payment_methods_keyboard.append(back_to_admin_home_page_button[0])
        await update.callback_query.edit_message_text(
            text="اختر وسيلة الدفع💳.",
            reply_markup=InlineKeyboardMarkup(payment_methods_keyboard),
        )
        return PAYMENT_METHOD_TO_TURN_ON_OR_OFF


async def turn_user_calls_on_or_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        if not context.bot_data["data"].get("user_calls", False):
            context.bot_data["data"]["user_calls"] = {
                "withdraw": True,
                "deposit": True,
                "buy_usdt": True,
                "create_account": True,
                "make_complaint": True,
            }

        await update.callback_query.edit_message_text(
            text="اختر الزر🔘", reply_markup=InlineKeyboardMarkup(turn_user_calls_on_or_off_keyboard)
        )
        return USER_CALL_TO_TURN_ON_OR_OFF


async def user_call_to_turn_on_or_off(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        data = update.callback_query.data[1:]
        if context.bot_data["data"]["user_calls"].get(data, None) == None:
            context.bot_data["data"]["user_calls"][data] = True

        if context.bot_data["data"]["user_calls"][data]:
            context.bot_data["data"]["user_calls"][data] = False
            await update.callback_query.answer("تم إيقاف الزر⛔️")
        else:
            context.bot_data["data"]["user_calls"][data] = True
            await update.callback_query.answer("تم تشغيل الزر✅")

        await update.callback_query.edit_message_text(
            text="اختر الزر🔘", reply_markup=InlineKeyboardMarkup(turn_user_calls_on_or_off_keyboard)
        )
        return USER_CALL_TO_TURN_ON_OR_OFF


turn_payment_method_on_or_off_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            turn_payment_method_on_or_off, "^turn payment method on or off$"
        )
    ],
    states={
        PAYMENT_METHOD_TO_TURN_ON_OR_OFF: [
            CallbackQueryHandler(
                payment_method_to_turn_on_or_off, payment_method_pattern
            )
        ]
    },
    fallbacks=[back_to_admin_home_page_handler, admin_command],
)

turn_user_calls_on_or_off_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(turn_user_calls_on_or_off, "^turn user calls on or off$")
    ],
    states={
        USER_CALL_TO_TURN_ON_OR_OFF: [
            CallbackQueryHandler(
                user_call_to_turn_on_or_off,
                "^a(withdraw|deposit|buy usdt|create account|make complaint)$",
            )
        ]
    },
    fallbacks=[back_to_admin_home_page_handler, admin_command],
)



hide_ids_keyboard_handler = CallbackQueryHandler(
    callback=hide_ids_keyboard, pattern="^hide ids keyboard$"
)

find_id_handler = MessageHandler(
    filters=filters.StatusUpdate.USER_SHARED | filters.StatusUpdate.CHAT_SHARED,
    callback=find_id,
)
