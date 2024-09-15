from telegram import Update, Chat, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    filters,
    MessageHandler,
)
from custom_filters import Admin, DepositAgent
from common.common import (
    build_back_button,
    build_admin_keyboard,
    build_worker_keyboard,
    payment_method_pattern,
    format_amount,
)
from common.back_to_home_page import (
    back_to_admin_home_page_button,
    back_to_admin_home_page_handler,
)
from models import Wallet
from admin.wallet_settings.common import (
    CHOOSE_METHOD,
    build_wallets_keyboard,
    choose_wallet_settings_option,
)
from start import admin_command, worker_command

WALLET, UPDATE_OPTION, NEW_VALUE = range(1, 4)


async def choose_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and (
        Admin().filter(update) or DepositAgent().filter(update)
    ):
        if not update.callback_query.data.startswith("back"):
            method = update.callback_query.data
            context.user_data["update_wal_method"] = method
        else:
            method = context.user_data["update_wal_method"]
        wallets = Wallet.get_wallets(method=method)
        if not wallets:
            await update.callback_query.answer(
                text=f"ليس لديك محافظ {method} بعد",
                show_alert=True,
            )
            return
        wallets_keyboard = build_wallets_keyboard(wallets)
        wallets_keyboard.append(build_back_button("back_to_choose_method"))
        wallets_keyboard.append(back_to_admin_home_page_button[0])
        await update.callback_query.edit_message_text(
            text="اختر المحفظة التي تريد تعديلها",
            reply_markup=InlineKeyboardMarkup(wallets_keyboard),
        )
        return WALLET


back_to_choose_method = choose_wallet_settings_option


async def choose_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and (
        Admin().filter(update) or DepositAgent().filter(update)
    ):
        if not update.callback_query.data.startswith("back"):
            wal_num = update.callback_query.data
            context.user_data["update_wallet_number"] = wal_num
        else:
            wal_num = context.user_data["update_wallet_number"]
        update_wallet_keyboard = [
            InlineKeyboardButton(
                text="الحد المسموح",
                callback_data="update_wallet_limit",
            ),
            InlineKeyboardButton(
                text="الرصيد",
                callback_data="update_wallet_balance",
            ),
            *build_back_button("back_to_choose_wallet"),
            *back_to_admin_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text="تعديل:",
            reply_markup=InlineKeyboardMarkup.from_column(update_wallet_keyboard),
        )
        return UPDATE_OPTION


back_to_choose_wallet = choose_method


async def choose_update_wallet_option(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE and (
        Admin().filter(update) or DepositAgent().filter(update)
    ):
        update_option_dict = {
            "balance": "الرصيد",
            "limit": "الحد المسموح",
        }
        back_buttons = [
            build_back_button("back_to_choose_update_wallet_option"),
            back_to_admin_home_page_button[0],
        ]
        if not update.callback_query.data.startswith("back"):
            update_option = update.callback_query.data.split("_")[-1]
            context.user_data["update_wallet_option"] = update_option
        else:
            update_option = context.user_data["update_wallet_option"]
        wal = Wallet.get_wallets(
            method=context.user_data["update_wal_method"],
            number=context.user_data["update_wallet_number"],
        )
        cur_val = getattr(wal, update_option)
        await update.callback_query.edit_message_text(
            text=(
                f"أرسل قيمة {update_option_dict[update_option]} الجديدة\n"
                f"القيمة الحالية: <b>{format_amount(cur_val) if isinstance(cur_val, float) else cur_val}</b>"
            ),
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return NEW_VALUE


back_to_choose_update_wallet_option = choose_wallet


async def get_new_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and (
        Admin().filter(update) or DepositAgent().filter(update)
    ):
        new_val = update.message.text
        await Wallet.update_wallets(
            method=context.user_data["update_wal_method"],
            number=context.user_data["update_wallet_number"],
            option=context.user_data["update_wallet_option"],
            value=new_val,
        )
        await update.message.reply_text(
            text="تم التعديل بنجاح ✅",
            reply_markup=(
                build_admin_keyboard()
                if Admin().filter(update)
                else build_worker_keyboard(deposit_agent=True)
            ),
        )
        return ConversationHandler.END


update_wallet_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            choose_wallet_settings_option,
            "^update_wallet$",
        )
    ],
    states={
        CHOOSE_METHOD: [
            CallbackQueryHandler(
                choose_method,
                payment_method_pattern,
            )
        ],
        WALLET: [
            CallbackQueryHandler(
                choose_wallet,
                "^\d+$",
            ),
        ],
        UPDATE_OPTION: [
            CallbackQueryHandler(
                choose_update_wallet_option,
                "^update_wallet_((balance)|(limit))$",
            )
        ],
        NEW_VALUE: [
            MessageHandler(
                filters=filters.Regex("^\d+.?\d*$"),
                callback=get_new_value,
            )
        ],
    },
    fallbacks=[
        admin_command,
        worker_command,
        back_to_admin_home_page_handler,
        CallbackQueryHandler(back_to_choose_method, "^back_to_choose_method$"),
        CallbackQueryHandler(back_to_choose_wallet, "^back_to_choose_wallet$"),
        CallbackQueryHandler(
            back_to_choose_update_wallet_option, "back_to_choose_update_wallet_option"
        ),
    ],
)
