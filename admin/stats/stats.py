from telegram import Update, Chat, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from custom_filters import Admin
from admin.stats.common import build_stats_keyboard
from common.stringifies import stringify_daily_order_stats, stringify_daily_wallet_stats
from common.constants import *
from common.back_to_home_page import back_to_admin_home_page_button
import models


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        keyboard = build_stats_keyboard()
        keyboard.append(back_to_admin_home_page_button[0])
        await update.callback_query.edit_message_text(
            text="الإحصائيات",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def choose_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        if update.callback_query.data.startswith("deposit"):
            text = stringify_daily_order_stats(
                "إيداعات",
                stats=models.DepositOrder.calc_daily_stats(),
            )
        elif update.callback_query.data.startswith("withdraw"):
            text = stringify_daily_order_stats(
                "سحوبات",
                stats=models.WithdrawOrder.calc_daily_stats(),
            )
        else:
            text = ""
            for method in PAYMENT_METHODS_LIST:
                wallets_stats = models.Wallet.get_wallets(method=method)
                if not wallets_stats:
                    continue

                text += (
                    stringify_daily_wallet_stats(method=method, stats=wallets_stats)
                    + "\n\n"
                )
        await update.callback_query.delete_message()
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text=text + "\nاضغط /admin للمتابعة",
        )


stats_handler = CallbackQueryHandler(stats, "^stats$")
choose_stats_handler = CallbackQueryHandler(
    choose_stats, "^((deposit)|(withdraw)|(wallets))_stats$"
)
