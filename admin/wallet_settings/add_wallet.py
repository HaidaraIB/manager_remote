from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, Chat
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
from common.constants import SYRCASH
from start import admin_command, start_command, worker_command
from models import Wallet

NUMBER, WALLET_TYPE, LIMIT = 1, 2, 3


async def choose_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and (
        Admin().filter(update) or DepositAgent().filter(update)
    ):
        if not update.callback_query.data.startswith("back"):
            method = update.callback_query.data
            context.user_data["wallet_settings_method"] = method
        else:
            method = context.user_data["wallet_settings_method"]
        if method == SYRCASH:
            keyboard = [
                [
                    InlineKeyboardButton(
                        text="تجارية",
                        callback_data="commercial_wallet",
                    ),
                    InlineKeyboardButton(
                        text="عادية",
                        callback_data="regular_wallet",
                    ),
                ],
                build_back_button("back_to_wallets_settings"),
                back_to_admin_home_page_button[0],
            ]
            text = f"اختر نوع محفظة {method}"
            ret = WALLET_TYPE
        else:
            context.user_data["wallet_settings_wallet_type"] = "regular"
            keyboard = [
                build_back_button("back_to_wallets_settings"),
                back_to_admin_home_page_button[0],
            ]
            text = (
                f"أرسل محفظة {method} جديدة\n\n"
                "<i><b>ملاحظة:</b></i> سيتم تهيئة رصيد المحفظة بالقيمة 0 تأكد من أنها فارغة بالفعل."
            )
            ret = NUMBER

        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return ret


back_to_wallets_settings = choose_wallet_settings_option


async def choose_wallet_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and (
        Admin().filter(update) or DepositAgent().filter(update)
    ):
        if not update.callback_query.data.startswith("back"):
            wallet_type = update.callback_query.data.split("_")[0]
            context.user_data["wallet_settings_wallet_type"] = wallet_type
        else:
            wallet_type = context.user_data["wallet_settings_wallet_type"]

        method = context.user_data["wallet_settings_method"]
        keyboard = [
            build_back_button("back_to_choose_wallet_type"),
            back_to_admin_home_page_button[0],
        ]
        text = (
            f"أرسل محفظة {method} جديدة\n\n"
            "<i><b>ملاحظة:</b></i> سيتم تهيئة رصيد المحفظة بالقيمة 0 تأكد من أنها فارغة بالفعل."
        )
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return NUMBER


back_to_choose_wallet_type = choose_method


async def get_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and (
        Admin().filter(update) or DepositAgent().filter(update)
    ):
        wallet_type = context.user_data["wallet_settings_wallet_type"]
        back_buttons = [
            build_back_button(f"back_to_get_number_{wallet_type}"),
            back_to_admin_home_page_button[0],
        ]
        if update.message:
            number = update.message.text
            method = context.user_data["wallet_settings_method"]

            wal = Wallet.get_wallets(
                method=context.user_data["wallet_settings_method"], number=number
            )
            if wal:
                back_buttons = [
                    build_back_button(
                        "back_to_wallets_settings"
                        if method != SYRCASH
                        else "back_to_choose_wallet_type"
                    ),
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


back_to_get_number_regular = choose_method
back_to_get_number_commercial = choose_wallet_type


async def get_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and (
        Admin().filter(update) or DepositAgent().filter(update)
    ):
        wallet_type = context.user_data["wallet_settings_wallet_type"]
        await Wallet.add_wallet(
            number=context.user_data["wallet_settings_number"],
            limit=float(update.message.text),
            method=context.user_data["wallet_settings_method"],
            is_commercial=wallet_type == "commercial",
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
        WALLET_TYPE: [
            CallbackQueryHandler(
                choose_wallet_type,
                "^((regular)|(commercial))_wallet$",
            )
        ],
        NUMBER: [
            MessageHandler(
                filters=filters.Regex(r"^P?[0-9]+$"),
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
            back_to_get_number_regular,
            "^back_to_get_number_regular$",
        ),
        CallbackQueryHandler(
            back_to_get_number_commercial,
            "^back_to_get_number_commercial$",
        ),
        CallbackQueryHandler(
            back_to_choose_wallet_type,
            "^back_to_choose_wallet_type$",
        ),
        admin_command,
        start_command,
        worker_command,
        back_to_admin_home_page_handler,
    ],
)
