from telegram import Update, Chat, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler
from custom_filters import Admin
from user.work_with_us.common import govs_pattern
from common.common import build_back_button
from common.back_to_home_page import (
    back_to_admin_home_page_button,
    back_to_admin_home_page_handler,
)
from admin.agent_settings.common import GOV, choose_agent_settings_option
from admin.agent_settings.agent_settings import back_to_agent_settings
import models

AGENT = 1


async def choose_gov_or_agent_to_remove(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        if not update.callback_query.data.startswith("back"):
            gov = update.callback_query.data.split("_")[0]
            context.user_data["gov_to_remove_agent_from"] = gov
        else:
            gov = context.user_data["gov_to_remove_agent_from"]

        if update.callback_query.data.isnumeric():
            await models.TrustedAgent.remove_worker(
                worker_id=int(update.callback_query.data),
                gov=gov,
            )
            await update.callback_query.answer(
                text="تمت الإزالة بنجاح ✅",
                show_alert=True,
            )

        agents = models.TrustedAgent.get_workers(gov=gov)

        if not agents:
            await choose_agent_settings_option(update, context)
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


remove_agent_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            choose_agent_settings_option,
            "^remove_agent$",
        )
    ],
    states={
        GOV: [
            CallbackQueryHandler(
                choose_gov_or_agent_to_remove,
                govs_pattern,
            )
        ],
        AGENT: [
            CallbackQueryHandler(
                choose_gov_or_agent_to_remove,
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
