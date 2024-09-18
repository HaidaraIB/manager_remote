from telegram import Update, InlineKeyboardMarkup, Chat
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from custom_filters import DepositAgent, Admin
from admin.wallet_settings.common import choose_wallet_settings_option, CHOOSE_METHOD
from common.common import (
    build_admin_keyboard,
    build_worker_keyboard,
    payment_method_pattern,
    build_back_button,
)
from common.back_to_home_page import (
    back_to_admin_home_page_handler,
    back_to_admin_home_page_button,
)
from start import admin_command, start_command, worker_command
from models import Wallet

NUMBER, LIMIT = 1, 2


async def choose_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and (
        Admin().filter(update) or DepositAgent().filter(update)
    ):
        back_buttons = [
            build_back_button("back_to_wallets_settings"),
            back_to_admin_home_page_button[0],
        ]

        if not update.callback_query.data.startswith("back"):
            context.user_data["wallet_settings_method"] = update.callback_query.data

        text = (
            f"أرسل محفظة {update.callback_query.data} جديدة\n\n"
            "<i><b>ملاحظة:</b></i> سيتم تهيئة رصيد المحفظة بالقيمة 0 تأكد من أنها فارغة بالفعل."
        )

        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return NUMBER


back_to_wallets_settings = choose_wallet_settings_option


async def get_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and (
        Admin().filter(update) or DepositAgent().filter(update)
    ):
        back_buttons = [
            build_back_button("back_to_get_number"),
            back_to_admin_home_page_button[0],
        ]
        if update.message:
            number = update.message.text

            wal = Wallet.get_wallets(
                method=context.user_data["wallet_settings_method"], number=number
            )
            if wal:
                back_buttons = [
                    build_back_button("back_to_wallets_settings"),
                    back_to_admin_home_page_button[0],
                ]
                await update.message.reply_text(
                    text="هذه المحفظة موجودة لدينا",
                    reply_markup=InlineKeyboardMarkup(back_buttons),
                )
                return

            context.user_data["wallet_settings_number"] = number
            await update.message.reply_text(
                text="أرسل قيمة الحد المسموح",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        else:
            await update.callback_query.edit_message_text(
                text="أرسل قيمة الحد المسموح",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        return LIMIT


back_to_get_number = choose_method


async def get_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and (
        Admin().filter(update) or DepositAgent().filter(update)
    ):
        await Wallet.add_wallet(
            number=context.user_data["wallet_settings_number"],
            limit=float(update.message.text),
            method=context.user_data["wallet_settings_method"],
        )
        await update.message.reply_text(
            text="تمت إضافة المحفظة بنجاح ✅",
            reply_markup=(
                build_admin_keyboard()
                if Admin().filter(update)
                else build_worker_keyboard(deposit_agent=True)
            ),
        )
        return ConversationHandler.END


add_wallet_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            choose_wallet_settings_option,
            "^add_wallet$",
        ),
    ],
    states={
        CHOOSE_METHOD: [
            CallbackQueryHandler(
                choose_method,
                payment_method_pattern,
            )
        ],
        NUMBER: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=get_number,
            )
        ],
        LIMIT: [
            MessageHandler(
                filters=filters.Regex("^\d+$"),
                callback=get_limit,
            )
        ],
    },
    fallbacks=[
        CallbackQueryHandler(
            back_to_wallets_settings,
            "^back_to_wallets_settings$",
        ),
        CallbackQueryHandler(
            back_to_get_number,
            "^back_to_get_number$",
        ),
        admin_command,
        start_command,
        worker_command,
        back_to_admin_home_page_handler,
    ],
)
