from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Chat
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler
from custom_filters import DepositAgent, Admin
from common.common import build_methods_keyboard, build_back_button
from common.back_to_home_page import back_to_admin_home_page_button
from models import Wallet

CHOOSE_METHOD, WALLET = 0, 1


def build_choose_proccess_to_turn_method_on_or_off_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(
                text="سحب 💳", callback_data="turn_withdraw_on_or_off"
            ),
            InlineKeyboardButton(
                text="إيداع 📥", callback_data="turn_deposit_on_or_off"
            ),
        ],
        [
            InlineKeyboardButton(
                text="شراء USDT 💰",
                callback_data="turn_busdt_on_or_off",
            )
        ],
    ]
    return keyboard


def build_wallets_keyboard(wallets: list[Wallet], op: str):
    wallets_keyboard: list[list] = []
    for i in range(0, len(wallets), 2):
        row = []
        row.append(
            InlineKeyboardButton(
                text=wallets[i].number,
                callback_data=f"{op}_{wallets[i].number}",
            )
        )
        if i + 1 < len(wallets):
            row.append(
                InlineKeyboardButton(
                    text=wallets[i + 1].number,
                    callback_data=f"{op}_{wallets[i + 1].number}",
                )
            )
        wallets_keyboard.append(row)
    return wallets_keyboard


def build_wallet_settings_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(
                text="إضافة محفظة ➕",
                callback_data="add_wallet",
            ),
            InlineKeyboardButton(
                text="تعديل محفظة 🔄",
                callback_data="update_wallet",
            ),
        ],
        [
            InlineKeyboardButton(
                text="حذف محفظة 🗑",
                callback_data="remove_wallet",
            ),
            InlineKeyboardButton(
                text="تصفير محافظ 0️⃣",
                callback_data="clear_wallets",
            ),
        ],
        [
            InlineKeyboardButton(
                text="عرض محفظة 🔎",
                callback_data="show_wallet",
            ),
        ],
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
        if not update.callback_query.data.startswith("back"):
            context.user_data["wallet_setting"] = update.callback_query.data.split("_")[
                0
            ]
        await reply_with_payment_methods(update)
        return CHOOSE_METHOD


async def reply_with_payment_methods(update: Update):
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


back_to_choose_wallet_settings_option = wallet_settings


async def choose_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and (
        Admin().filter(update) or DepositAgent().filter(update)
    ):
        if not update.callback_query.data.startswith("back"):
            method = update.callback_query.data
            context.user_data["wallet_setting_method"] = method
        else:
            method = context.user_data["wallet_setting_method"]

        res = await reply_with_wallets(method, update, context)
        if not res:
            return

        return WALLET


async def reply_with_wallets(
    method: str, update: Update, context: ContextTypes.DEFAULT_TYPE
):
    wallets = Wallet.get_wallets(method=method)
    if not wallets:
        await update.callback_query.answer(
            text=f"ليس لديك محافظ {method} بعد",
            show_alert=True,
        )
        return False
    update_or_remove = {
        "remove": "حذفها",
        "update": "تعديلها",
        "show": "عرضها",
    }
    wallets_keyboard = build_wallets_keyboard(
        wallets, context.user_data["wallet_setting"]
    )
    wallets_keyboard.append(build_back_button("back_to_choose_method"))
    wallets_keyboard.append(back_to_admin_home_page_button[0])
    await update.callback_query.edit_message_text(
        text=f"اختر المحفظة التي تريد {update_or_remove[context.user_data['wallet_setting']]}",
        reply_markup=InlineKeyboardMarkup(wallets_keyboard),
    )
    return True


back_to_choose_method = choose_wallet_settings_option


wallet_settings_handler = CallbackQueryHandler(wallet_settings, "^wallets settings$")
back_to_choose_wallet_settings_option_handler = CallbackQueryHandler(
    back_to_choose_wallet_settings_option, "^back_to_choose_wallet_settings_option$"
)
