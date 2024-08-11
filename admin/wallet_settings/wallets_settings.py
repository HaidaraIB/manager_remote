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


from custom_filters import DepositAgent, Admin

from common.common import (
    build_methods_keyboard,
    build_admin_keyboard,
    build_worker_keyboard,
    payment_method_pattern,
    build_back_button,
)

from common.back_to_home_page import (
    back_to_admin_home_page_handler,
    back_to_admin_home_page_button,
)

from admin.wallet_settings.common import *

from start import admin_command, start_command, worker_command
from common.constants import *

(
    CHOOSE_METHOD_TO_UPDATE,
    CHOOSE_NUMBER,
    NEW_CODE,
) = range(3)


async def wallets_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and (
        Admin().filter(update) or DepositAgent().filter(update)
    ):
        methods = build_methods_keyboard()
        methods.append(back_to_admin_home_page_button[0])
        await update.callback_query.edit_message_text(
            text="اختر وسيلة الدفع💳.",
            reply_markup=InlineKeyboardMarkup(methods),
        )
        return CHOOSE_METHOD_TO_UPDATE


async def choose_method_to_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and (
        Admin().filter(update) or DepositAgent().filter(update)
    ):
        back_buttons = [
            build_back_button("back_to_wallets_settings"),
            back_to_admin_home_page_button[0],
        ]
        method = update.callback_query.data

        if not update.callback_query.data.startswith("back"):
            context.user_data["wallet_settings_method"] = method
        else:
            method = context.user_data["wallet_settings_method"]

        if method in AEBAN_LIST:
            numbers_keyboard = [
                [
                    InlineKeyboardButton(
                        text="رقم الآيبان", callback_data="change_aeban"
                    ),
                    InlineKeyboardButton(
                        text="رقم الحساب", callback_data="change_number"
                    ),
                ],
                *back_buttons,
            ]
            await update.callback_query.edit_message_text(
                text="اختر ما الذي تريد تعديله",
                reply_markup=InlineKeyboardMarkup(numbers_keyboard),
            )
            return CHOOSE_NUMBER
        context.user_data["aeban_or_number"] = "number"
        try:
            context.bot_data["data"][f"{method}_number"]
        except KeyError:
            context.bot_data["data"][f"{method}_number"] = 123456

        await update.callback_query.edit_message_text(
            text=(
                f"أرسل رقم حساب {method} الجديد 🔢\n\n"
                f"الرقم الحالي: <code>{context.bot_data['data'][f'{method}_number']}</code>"
            ),
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return NEW_CODE


back_to_wallets_settings = wallets_settings


async def choose_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and (
        Admin().filter(update) or DepositAgent().filter(update)
    ):
        back_buttons = [
            build_back_button("back_to_choose_number"),
            back_to_admin_home_page_button[0],
        ]
        aeban_or_number = update.callback_query.data.split("_")[-1]
        method = context.user_data["wallet_settings_method"]
        context.user_data["aeban_or_number"] = aeban_or_number

        try:
            context.bot_data["data"][f"{method}_{aeban_or_number}"]
        except KeyError:
            context.bot_data["data"][f"{method}_{aeban_or_number}"] = "123456"

        await update.callback_query.edit_message_text(
            text=(
                f"أرسل رقم {aeban_or_number_dict[aeban_or_number]} {method} الجديد 🔢\n\n"
                f"الرقم الحالي: <code>{context.bot_data['data'][f'{method}_{aeban_or_number}']}</code>"
            ),
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return NEW_CODE


back_to_choose_number = choose_method_to_update


async def new_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and (
        Admin().filter(update) or DepositAgent().filter(update)
    ):
        aeban_or_number = context.user_data["aeban_or_number"]
        context.bot_data["data"][
            f"{context.user_data['wallet_settings_method']}_{aeban_or_number}"
        ] = update.message.text
        text = f"تم تغيير رقم {aeban_or_number_dict[aeban_or_number]} <b>{context.user_data['wallet_settings_method']}</b> بنجاح ✅"

        await update.message.reply_text(
            text=text,
            reply_markup=(
                build_admin_keyboard()
                if Admin().filter(update)
                else build_worker_keyboard(deposit_agent=True)
            ),
        )
        return ConversationHandler.END


wallets_settings_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            wallets_settings,
            "^wallets settings$",
        ),
    ],
    states={
        CHOOSE_METHOD_TO_UPDATE: [
            CallbackQueryHandler(
                choose_method_to_update,
                payment_method_pattern,
            )
        ],
        CHOOSE_NUMBER: [
            CallbackQueryHandler(
                choose_number,
                "^change_((aeban)|(number))$",
            )
        ],
        NEW_CODE: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=new_code,
            )
        ],
    },
    fallbacks=[
        CallbackQueryHandler(
            back_to_wallets_settings,
            "^back_to_wallets_settings$",
        ),
        CallbackQueryHandler(
            back_to_choose_number,
            "^back_to_choose_number$",
        ),
        admin_command,
        start_command,
        worker_command,
        back_to_admin_home_page_handler,
    ],
)
