from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Chat
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler
from custom_filters import DepositAgent, Admin
from common.common import build_methods_keyboard, build_back_button
from common.back_to_home_page import back_to_admin_home_page_button
from models import Wallet

CHOOSE_METHOD = 0


def build_wallets_keyboard(wallets: list[Wallet]):
    wallets_keyboard: list[list] = []
    for i in range(0, len(wallets), 2):
        row = []
        row.append(
            InlineKeyboardButton(
                text=wallets[i].number,
                callback_data=wallets[i].number,
            )
        )
        if i + 1 < len(wallets):
            row.append(
                InlineKeyboardButton(
                    text=wallets[i + 1].number,
                    callback_data=wallets[i + 1].number,
                )
            )
        wallets_keyboard.append(row)
    return wallets_keyboard


def build_wallet_settings_keyboard():
    keyboard = [
        [InlineKeyboardButton(text="إضافة محفظة ➕", callback_data="add_wallet")],
        [InlineKeyboardButton(text="تعديل محفظة 🔄", callback_data="update_wallet")],
        [InlineKeyboardButton(text="تصفير محافظ 0️⃣", callback_data="clear_wallets")],
        [
            InlineKeyboardButton(
                text="تفعيل/إلغاء تفعيل وسيلة دفع 🔂",
                callback_data="turn payment method on or off",
            )
        ],
    ]
    return keyboard


async def wallet_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and (
        Admin().filter(update) or DepositAgent().filter(update)
    ):
        keyboard = build_wallet_settings_keyboard()
        keyboard.append(back_to_admin_home_page_button[0])
        await update.callback_query.edit_message_text(
            text="اختر ماذا تريد أن تفعل؟",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return ConversationHandler.END


async def choose_wallet_settings_option(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE and (
        Admin().filter(update) or DepositAgent().filter(update)
    ):
        methods = build_methods_keyboard()
        methods.append(
            [
                InlineKeyboardButton(
                    text="محفظة طلبات الوكيل",
                    callback_data="طلبات الوكيل",
                )
            ]
        )
        methods.append(build_back_button("back_to_choose_wallet_settings_option"))
        methods.append(back_to_admin_home_page_button[0])
        await update.callback_query.edit_message_text(
            text="اختر وسيلة الدفع💳.",
            reply_markup=InlineKeyboardMarkup(methods),
        )
        return CHOOSE_METHOD


back_to_choose_wallet_settings_option = wallet_settings

wallet_settings_handler = CallbackQueryHandler(wallet_settings, "^wallets settings$")
back_to_choose_wallet_settings_option_handler = CallbackQueryHandler(
    back_to_choose_wallet_settings_option, "^back_to_choose_wallet_settings_option$"
)
