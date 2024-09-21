from telegram import Update, Chat, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler
from custom_filters import DepositAgent, Admin
from common.back_to_home_page import (
    back_to_admin_home_page_button,
    back_to_admin_home_page_handler,
)
from common.common import (
    build_admin_keyboard,
    payment_method_pattern,
    build_confirmation_keyboard,
)
from models import Wallet
from admin.wallet_settings.common import CHOOSE_METHOD, choose_wallet_settings_option
from start import admin_command, worker_command

CONFIRM_CLEAR_WALLETS = 1


async def choose_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and (
        Admin().filter(update) or DepositAgent().filter(update)
    ):
        if not update.callback_query.data.startswith("back"):
            method = update.callback_query.data
            context.user_data["clear_wals_method"] = method
        else:
            method = context.user_data["clear_wals_method"]

        wallets = Wallet.get_wallets(method=method)
        if not wallets:
            await update.callback_query.answer(
                text=f"ليس لديك محافظ {method} بعد",
                show_alert=True,
            )
            return

        keyboard = [
            build_confirmation_keyboard("clear_wallets"),
            back_to_admin_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text=f"هل أنت متأكد من أنك تريد تصفير جميع محافظ {method}؟",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return CONFIRM_CLEAR_WALLETS


cancel_clear_wallets = choose_wallet_settings_option


async def confirm_clear_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and (
        Admin().filter(update) or DepositAgent().filter(update)
    ):
        await Wallet.update_wallets(
            method=context.user_data["clear_wals_method"],
            option="balance",
            value=0,
        )
        await update.callback_query.edit_message_text(
            text="تم التصفير بنجاح ✅",
            reply_markup=build_admin_keyboard(),
        )
        return ConversationHandler.END


clear_wallets_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            choose_wallet_settings_option,
            "^clear_wallets$",
        )
    ],
    states={
        CHOOSE_METHOD: [
            CallbackQueryHandler(
                choose_method,
                payment_method_pattern,
            )
        ],
        CONFIRM_CLEAR_WALLETS: [
            CallbackQueryHandler(
                confirm_clear_wallets,
                "^yes_clear_wallets$",
            )
        ],
    },
    fallbacks=[
        admin_command,
        worker_command,
        back_to_admin_home_page_handler,
        CallbackQueryHandler(cancel_clear_wallets, "^no_clear_wallets$"),
    ],
)
