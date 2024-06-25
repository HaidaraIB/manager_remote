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
from telegram.constants import (
    ParseMode,
)

from common import (
    build_admin_keyboard,
    build_methods_keyboard,
    payment_method_pattern,
    back_to_admin_home_page_handler,
    request_buttons,
    back_button
)

from start import start_command

from DB import DB
from custom_filters.Admin import Admin


(
    NEW_USDT_TO_SYP,
    PAYMENT_METHOD_TO_TURN_ON_OR_OFF,
    USER_CALL_TO_TURN_ON_OR_OFF,
) = range(3)

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


async def update_usdt_to_syp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        try:
            context.bot_data["data"]["usdt_to_syp"]
        except KeyError:
            context.bot_data["data"]["usdt_to_syp"] = 14200
        await update.callback_query.edit_message_text(
            text=f"أرسل سعر USDT مقابل الليرة السورية الجديد، السعر الحالي: <b>{context.bot_data['data']['usdt_to_syp']} SYP</b>",
            reply_markup=InlineKeyboardMarkup(back_button),
        )
        return NEW_USDT_TO_SYP


async def new_usdt_to_syp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        context.bot_data["data"]["usdt_to_syp"] = float(update.message.text)
        await update.message.reply_text(
            text="تم تعديل سعر USDT مقابل الليرة السورية بنجاح✅",
            reply_markup=build_admin_keyboard(),
        )
        return ConversationHandler.END


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
        payment_methods_keyboard.append(back_button[0])
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
        payment_methods_keyboard.append(back_button[0])
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
        keyboard = [
            [InlineKeyboardButton(text="سحب💳", callback_data="awithdraw")],
            [InlineKeyboardButton(text="إيداع™️", callback_data="adeposit")],
            [
                InlineKeyboardButton(
                    text="إنشاء حساب موثق™️", callback_data="acreate account"
                )
            ],
            [InlineKeyboardButton(text="شراء USDT", callback_data="abuy usdt")],
            [InlineKeyboardButton(text="إنشاء شكوى🗳", callback_data="amake complaint")],
            back_button[0],
        ]
        await update.callback_query.edit_message_text(
            text="اختر الزر🔘", reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return USER_CALL_TO_TURN_ON_OR_OFF


async def user_call_to_turn_on_or_off(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        data = update.callback_query.data[1:]
        if data == "withdraw":

            if context.bot_data["data"]["user_calls"].get("withdraw", None) == None:
                context.bot_data["data"]["user_calls"]["withdraw"] = True

            if context.bot_data["data"]["user_calls"]["withdraw"]:
                context.bot_data["data"]["user_calls"]["withdraw"] = False
                await update.callback_query.answer("تم إيقاف الزر⛔️")
            else:
                context.bot_data["data"]["user_calls"]["withdraw"] = True
                await update.callback_query.answer("تم تشغيل الزر✅")

        elif data == "deposit":

            if context.bot_data["data"]["user_calls"].get("deposit", None) == None:
                context.bot_data["data"]["user_calls"]["deposit"] = True

            if context.bot_data["data"]["user_calls"]["deposit"]:
                context.bot_data["data"]["user_calls"]["deposit"] = False
                await update.callback_query.answer("تم إيقاف الزر⛔️")
            else:
                context.bot_data["data"]["user_calls"]["deposit"] = True
                await update.callback_query.answer("تم تشغيل الزر✅")

        elif data == "create account":

            if (
                context.bot_data["data"]["user_calls"].get("create_account", None)
                == None
            ):
                context.bot_data["data"]["user_calls"]["create_account"] = True

            if context.bot_data["data"]["user_calls"]["create_account"]:
                context.bot_data["data"]["user_calls"]["create_account"] = False
                await update.callback_query.answer("تم إيقاف الزر⛔️")
            else:
                context.bot_data["data"]["user_calls"]["create_account"] = True
                await update.callback_query.answer("تم تشغيل الزر✅")

        elif data == "buy usdt":

            if context.bot_data["data"]["user_calls"].get("buy_usdt", None) == None:
                context.bot_data["data"]["user_calls"]["buy_usdt"] = True

            if context.bot_data["data"]["user_calls"]["buy_usdt"]:
                context.bot_data["data"]["user_calls"]["buy_usdt"] = False
                await update.callback_query.answer("تم إيقاف الزر⛔️")
            else:
                context.bot_data["data"]["user_calls"]["buy_usdt"] = True
                await update.callback_query.answer("تم تشغيل الزر✅")
        else:

            if (
                context.bot_data["data"]["user_calls"].get("make_complaint", None)
                == None
            ):
                context.bot_data["data"]["user_calls"]["make_complaint"] = True

            if context.bot_data["data"]["user_calls"]["make_complaint"]:
                context.bot_data["data"]["user_calls"]["make_complaint"] = False
                await update.callback_query.answer("تم إيقاف الزر⛔️")
            else:
                context.bot_data["data"]["user_calls"]["make_complaint"] = True
                await update.callback_query.answer("تم تشغيل الزر✅")

        keyboard = [
            [InlineKeyboardButton(text="سحب💳", callback_data="awithdraw")],
            [InlineKeyboardButton(text="إيداع™️", callback_data="adeposit")],
            [
                InlineKeyboardButton(
                    text="إنشاء حساب موثق™️", callback_data="acreate account"
                )
            ],
            [InlineKeyboardButton(text="شراء USDT", callback_data="abuy usdt")],
            [InlineKeyboardButton(text="إنشاء شكوى🗳", callback_data="amake complaint")],
            back_button[0],
        ]
        await update.callback_query.edit_message_text(
            text="اختر الزر🔘", reply_markup=InlineKeyboardMarkup(keyboard)
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
    fallbacks=[back_to_admin_home_page_handler, start_command],
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
    fallbacks=[back_to_admin_home_page_handler, start_command],
)


update_usdt_to_syp_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(update_usdt_to_syp, "^update usdt to syp$")],
    states={
        NEW_USDT_TO_SYP: [
            MessageHandler(
                filters=filters.Regex("^\d+\.?\d*$"), callback=new_usdt_to_syp
            )
        ]
    },
    fallbacks=[back_to_admin_home_page_handler, start_command],
)


hide_ids_keyboard_handler = CallbackQueryHandler(callback=hide_ids_keyboard, pattern="^hide ids keyboard$")

find_id_handler = MessageHandler(
    filters=filters.StatusUpdate.USER_SHARED | filters.StatusUpdate.CHAT_SHARED,
    callback=find_id,
)