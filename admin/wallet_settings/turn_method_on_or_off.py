from telegram import Chat, Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler
from common.common import (
    build_methods_keyboard,
    payment_method_pattern,
    build_back_button,
)
from common.back_to_home_page import (
    back_to_admin_home_page_button,
    back_to_admin_home_page_handler,
)
from start import admin_command, start_command
from custom_filters import Admin
from models import PaymentMethod
from common.constants import *
from admin.wallet_settings.common import (
    back_to_choose_wallet_settings_option_handler,
    build_choose_proccess_to_turn_method_on_or_off_keyboard,
    build_methods_on_off_keyboard,
)

PROCCESS, PAYMENT_METHOD_TO_TURN_ON_OR_OFF = range(2)


async def turn_payment_method_on_or_off(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        keyboard = build_choose_proccess_to_turn_method_on_or_off_keyboard()
        keyboard.append(build_back_button("back_to_choose_wallet_settings_option"))
        keyboard.append(back_to_admin_home_page_button[0])
        await update.callback_query.edit_message_text(
            text="اختر العملية:", reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return PROCCESS


async def choose_proccess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        data = update.callback_query.data.replace("method_on_off ", "")
        if payment_method_pattern(callback_data=data):
            proccess = context.user_data["proccess_to_turn_method_on_or_off"]
            method = PaymentMethod.get_payment_method(name=data)
            if getattr(method, f"{proccess}_on_off"):
                text = "تم إيقاف وسيلة الدفع 🔴"
                on = 0
            else:
                text = "تم تشغيل وسيلة الدفع 🟢"
                on = 1
            await PaymentMethod.turn_payment_method_on_or_off(
                name=data, proccess=proccess, on=on
            )
            await update.callback_query.answer(
                text=text,
                show_alert=True,
            )
        else:
            proccess = data.split("_")[1]
            context.user_data["proccess_to_turn_method_on_or_off"] = proccess

        payment_methods_keyboard = build_methods_on_off_keyboard(proccess)
        payment_methods_keyboard.append(build_back_button("back_to_choose_proccess"))
        payment_methods_keyboard.append(back_to_admin_home_page_button[0])
        await update.callback_query.edit_message_text(
            text="اختر وسيلة الدفع💳.",
            reply_markup=InlineKeyboardMarkup(payment_methods_keyboard),
        )
        return PAYMENT_METHOD_TO_TURN_ON_OR_OFF


back_to_choose_proccess = turn_payment_method_on_or_off

turn_payment_method_on_or_off_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            turn_payment_method_on_or_off,
            "^turn payment method on or off$",
        )
    ],
    states={
        PROCCESS: [
            CallbackQueryHandler(
                choose_proccess, "^turn_((withdraw)|(deposit)|(busdt))_on_or_off$"
            )
        ],
        PAYMENT_METHOD_TO_TURN_ON_OR_OFF: [
            CallbackQueryHandler(
                choose_proccess,
                "^method_on_off",
            )
        ],
    },
    fallbacks=[
        back_to_admin_home_page_handler,
        admin_command,
        start_command,
        back_to_choose_wallet_settings_option_handler,
        CallbackQueryHandler(back_to_choose_proccess, "^back_to_choose_proccess$"),
    ],
)
