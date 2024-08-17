from telegram import (
    Update,
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
from common.common import build_back_button, build_agent_keyboard
from common.back_to_home_page import (
    back_to_agent_home_page_button,
    back_to_agent_home_page_handler,
)
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

REF_NUM = 2


async def get_player_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Agent().filter(update):
        text = (
            f"قم بإرسال المبلغ المراد إيداعه إلى:\n\n"
            f"<code>{context.bot_data['data'][f'{SYRCASH}_number']}</code>\n\n"
            f"ثم أرسل رقم عملية الدفع إلى البوت لنقوم بتوثيقها.\n\n"
        )
        back_buttons = [
            build_back_button("back_to_send_to_check_deposit"),
            back_to_agent_home_page_button[0],
        ]
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        else:
            context.user_data["player_number"] = update.message.text
            await update.message.reply_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        return REF_NUM


back_to_send_to_check_deposit = choose_point


async def get_ref_num(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Agent().filter(update):
        res = await send_to_check_deposit(
            context=context,
            user_id=update.effective_user.id,
            ref_num=update.message.text,
            acc_number=context.user_data["player_number"],
            method=SYRCASH,
            target_group=context.bot_data["data"]["deposit_orders_group"],
            agent_id=update.effective_user.id,
            gov=context.user_data[f"{context.user_data['agent_option']}_point"],
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
