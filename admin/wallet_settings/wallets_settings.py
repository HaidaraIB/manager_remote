from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Chat,
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

from custom_filters.Admin import Admin

from common.common import (
    build_methods_keyboard,
    build_admin_keyboard,
    payment_method_pattern,
)

from common.back_to_home_page import (
    back_to_admin_home_page_handler,
    back_to_admin_home_page_button
)

from start import start_command

(CHOOSE_METHOD_TO_UPDATE, NEW_CODE) = range(2)

async def wallets_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        methods = build_methods_keyboard()
        methods.append(back_to_admin_home_page_button[0])
        await update.callback_query.edit_message_text(
            text="اختر وسيلة الدفع💳.", reply_markup=InlineKeyboardMarkup(methods)
        )
        return CHOOSE_METHOD_TO_UPDATE


async def choose_method_to_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        back_buttons = [
            [
                InlineKeyboardButton(
                    text="الرجوع🔙", callback_data="back to wallets settings"
                )
            ],
            back_to_admin_home_page_button[0],
        ]

        context.user_data["wallet_settings_method"] = update.callback_query.data

        try:
            context.bot_data["data"][f"{update.callback_query.data}_number"]
        except KeyError:
            context.bot_data["data"][f"{update.callback_query.data}_number"] = 123456

        text = f"أرسل رقم حساب {update.callback_query.data} الجديد🔢\n\الرقم الحالي الحالي: <code>{context.bot_data['data'][f"{update.callback_query.data}_number"]}</code>"

        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return NEW_CODE


back_to_wallets_settings = wallets_settings


async def new_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):

        context.bot_data["data"][f"{context.user_data["wallet_settings_method"]}_number"] = update.message.text
        text = f"تم تغيير رقم حساب <b>{context.user_data["wallet_settings_method"]}</b> ينجاح✅"

        await update.message.reply_text(
            text=text, reply_markup=build_admin_keyboard(),
        )
        return ConversationHandler.END


wallets_settings_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(wallets_settings, "^wallets settings$")],
    states={
        CHOOSE_METHOD_TO_UPDATE: [
            CallbackQueryHandler(
                choose_method_to_update, payment_method_pattern
            )
        ],
        NEW_CODE: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND, callback=new_code
            )
        ],
    },
    fallbacks=[
        start_command,
        back_to_admin_home_page_handler,
        CallbackQueryHandler(
            back_to_wallets_settings, "^back to wallets settings$"
        ),
    ],
)