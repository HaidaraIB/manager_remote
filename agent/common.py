from telegram import Update, Chat, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from common.back_to_home_page import back_to_agent_home_page_button
import models
from custom_filters import Agent
from common.decorators import check_if_user_agent_decorator
from common.common import build_back_button

POINT, PLAYER_NUMBER = range(2)


@check_if_user_agent_decorator
async def agent_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Agent().filter(update):
        if not update.callback_query.data.startswith("back"):
            context.user_data["agent_option"] = update.callback_query.data
        agent = models.TrustedAgent.get_workers(user_id=update.effective_user.id)
        points = [
            [InlineKeyboardButton(text=a.gov, callback_data=a.gov)] for a in agent
        ] + back_to_agent_home_page_button
        await update.callback_query.edit_message_text(
            text="اختر النقطة",
            reply_markup=InlineKeyboardMarkup(points),
        )
        return POINT


async def choose_point(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Agent().filter(update):
        if not update.callback_query.data.startswith("back"):
            context.user_data[f"{context.user_data['agent_option']}_point"] = (
                update.callback_query.data
            )
        back_buttons = [
            build_back_button("back_to_choose_point"),
            back_to_agent_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text="أرسل رقم حساب اللاعب",
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return PLAYER_NUMBER


back_to_choose_point = agent_option
