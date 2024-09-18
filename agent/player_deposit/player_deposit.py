from telegram import Update, InlineKeyboardMarkup, Chat
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from common.common import build_back_button, build_agent_keyboard
from common.back_to_home_page import (
    back_to_agent_home_page_button,
    back_to_agent_home_page_handler,
)
from models import Wallet
from common.constants import *
from start import agent_command
from agent.point_deposit.common import govs_pattern
from user.deposit.common import send_to_check_deposit
from custom_filters import Agent
from agent.common import (
    POINT,
    PLAYER_NUMBER,
    choose_point,
    agent_option,
    back_to_choose_point,
)

AMOUNT, REF_NUM = 2, 3


async def get_player_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Agent().filter(update):
        back_buttons = [
            build_back_button("back_to_send_to_check_deposit"),
            back_to_agent_home_page_button[0],
        ]
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text="أرسل قيمة الإيداع",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        else:
            context.user_data["player_number"] = update.message.text
            await update.message.reply_text(
                text="إرسل قيمة الإيداع",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        return AMOUNT


async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Agent().filter(update):
        if update.message:
            amount = float(update.message.text)
            context.user_data["player_deposit_amount"] = amount
        else:
            amount = context.user_data["player_deposit_amount"]

        wal = Wallet.get_wallets(amount=amount, method=SYRCASH)
        if not wal:
            await update.message.reply_text(
                text=(
                    "المبلغ المدخل تجاوز الحد المسموح لحسابات الشركة ❗️\n"
                    "جرب مع قيمة أصغر"
                )
            )
            return

        text = (
            f"قم بإرسال المبلغ المراد إيداعه إلى:\n\n"
            f"<code>{wal.number}</code>\n\n"
            f"ثم أرسل رقم عملية الدفع إلى البوت لنقوم بتوثيقها.\n\n"
        )
        back_buttons = [
            build_back_button("back_to_get_amount"),
            back_to_agent_home_page_button[0],
        ]
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        else:
            context.user_data["player_deposit_amount"] = float(update.message.text)
            await update.message.reply_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        return REF_NUM


back_to_send_to_check_deposit = choose_point


async def get_ref_num(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Agent().filter(update):
        res = await send_to_check_deposit(
            update=update, context=context, is_player_deposit=True
        )
        if not res:
            await update.message.reply_text(
                text="رقم عملية مكرر ❗️",
            )
            return

        await update.message.reply_text(
            text="شكراً لك، سيتم التحقق من العملية وإضافة المبلغ المودع خلال وقت قصير.",
            reply_markup=build_agent_keyboard(),
        )

        return ConversationHandler.END


player_deposit_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            agent_option,
            "^player_deposit$",
        )
    ],
    states={
        POINT: [
            CallbackQueryHandler(
                choose_point,
                govs_pattern,
            )
        ],
        PLAYER_NUMBER: [
            MessageHandler(
                filters=filters.Regex("^\d+$"),
                callback=get_player_number,
            )
        ],
        REF_NUM: [
            MessageHandler(
                filters=filters.Regex("^\d+$"),
                callback=get_ref_num,
            )
        ],
    },
    fallbacks=[
        CallbackQueryHandler(back_to_choose_point, "^back_to_choose_point$"),
        CallbackQueryHandler(
            back_to_send_to_check_deposit, "^back_to_send_to_check_deposit$"
        ),
        back_to_agent_home_page_handler,
        agent_command,
    ],
    name="player_deposit_handler",
    persistent=True,
)
