from telegram import Update, Chat, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler
from custom_filters import Admin
from user.work_with_us.common import govs_pattern
from common.stringifies import stringify_agent
from common.common import build_back_button
from common.back_to_home_page import (
    back_to_admin_home_page_button,
    back_to_admin_home_page_handler,
)
from admin.agent_settings.common import GOV, choose_agent_settings_option
from admin.agent_settings.agent_settings import back_to_agent_settings
import models

AGENT = 1


async def choose_gov(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        if not update.callback_query.data.startswith("back"):
            gov = update.callback_query.data.split("_")[0]
            context.user_data["gov_to_show_agent_from"] = gov
        else:
            gov = context.user_data["gov_to_show_agent_from"]

        agents = models.TrustedAgent.get_workers(gov=gov)
        if not agents:
            await update.callback_query.answer(
                text="ليس هناك وكلاء لهذه المحافظة",
                show_alert=True,
            )
            return GOV

        agents_keyboard = [
            [InlineKeyboardButton(text=agent.neighborhood, callback_data=agent.user_id)]
            for agent in agents
        ]
        agents_keyboard.append(build_back_button("back_to_choose_gov"))
        agents_keyboard.append(back_to_admin_home_page_button[0])
        await update.callback_query.edit_message_text(
            text="اختر الوكيل", reply_markup=InlineKeyboardMarkup(agents_keyboard)
        )
        return AGENT


back_to_choose_gov = choose_agent_settings_option


async def choose_agent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        agent = models.TrustedAgent.get_workers(
            gov=context.user_data["gov_to_show_agent_from"],
            user_id=int(update.callback_query.data),
        )
        await update.callback_query.edit_message_text(
            text=stringify_agent(agent),
            reply_markup=InlineKeyboardMarkup(back_to_admin_home_page_button),
        )
        return ConversationHandler.END


show_agent_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            choose_agent_settings_option,
            "^show_agent$",
        )
    ],
    states={
        GOV: [
            CallbackQueryHandler(
                choose_gov,
                govs_pattern,
            )
        ],
        AGENT: [
            CallbackQueryHandler(
                choose_agent,
                "^\d+$",
            )
        ],
    },
    fallbacks=[
        CallbackQueryHandler(back_to_choose_gov, "^back_to_choose_gov$"),
        CallbackQueryHandler(back_to_agent_settings, "^back_to_agent_settings$"),
        back_to_admin_home_page_handler,
    ],
)
