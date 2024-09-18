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
from admin.wallet_settings.common import back_to_choose_wallet_settings_option_handler

PAYMENT_METHOD_TO_TURN_ON_OR_OFF = 0


async def turn_payment_method_on_or_off(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        data = update.callback_query.data
        if payment_method_pattern(callback_data=data):
            method = PaymentMethod.get_payment_method(name=data)
            if method.on_off:
                await PaymentMethod.turn_payment_method_on_or_off(name=data)
                await update.callback_query.answer(
                    "تم إيقاف وسيلة الدفع ✅",
                    show_alert=True,
                )
            else:
                await PaymentMethod.turn_payment_method_on_or_off(name=data, on=1)
                await update.callback_query.answer(
                    "تم تشغيل وسيلة الدفع ✅",
                    show_alert=True,
                )
        payment_methods_keyboard = build_methods_keyboard()
        payment_methods_keyboard.append(
            build_back_button("back_to_choose_wallet_settings_option")
        )
        payment_methods_keyboard.append(back_to_admin_home_page_button[0])
        await update.callback_query.edit_message_text(
            text="اختر وسيلة الدفع💳.",
            reply_markup=InlineKeyboardMarkup(payment_methods_keyboard),
        )
        return PAYMENT_METHOD_TO_TURN_ON_OR_OFF


turn_payment_method_on_or_off_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            turn_payment_method_on_or_off,
            "^turn payment method on or off$",
        )
    ],
    states={
        PAYMENT_METHOD_TO_TURN_ON_OR_OFF: [
            CallbackQueryHandler(
                turn_payment_method_on_or_off,
                payment_method_pattern,
            )
        ]
    },
    fallbacks=[
        back_to_admin_home_page_handler,
        admin_command,
        start_command,
        back_to_choose_wallet_settings_option_handler,
    ],
)
