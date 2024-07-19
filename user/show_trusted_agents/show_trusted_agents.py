from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Chat

from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
)

from common.back_to_home_page import back_to_user_home_page_button
from models import TrustedAgent
from common.common import build_back_button
from common.back_to_home_page import (
    back_to_user_home_page_button,
    back_to_user_home_page_handler,
)
from user.work_with_us.common import (
    build_govs_keyboard,
    syrian_govs_en_ar,
    govs_pattern,
)
from start import start_command

(CHOOSE_GOV,) = range(1)


async def show_trusted_agents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        keyboard = build_govs_keyboard()
        keyboard.append(back_to_user_home_page_button[0])
        keyboard.insert(
            0,
            [
                InlineKeyboardButton(
                    text="وكيل مباشر 🛄",
                    url="http://t.me/Melbet_bo",
                ),
            ],
        )
        await update.callback_query.edit_message_text(
            text="اختر المحافظة", reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return CHOOSE_GOV


async def choose_gov(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        gov = update.callback_query.data.split("_")[0]
        trusted_agents = TrustedAgent.get_trusted_agents(gov=gov)
        if not trusted_agents:
            await update.callback_query.answer(
                text="لا يوجد وكلاء لهذه المحافظة بعد",
                show_alert=True,
            )
            return
        agents_tg_chats = [
            (await context.bot.get_chat(chat_id=agent.user_id))
            for agent in trusted_agents
        ]
        keyboard = [
            [
                InlineKeyboardButton(
                    text=agent.full_name, url=f"t.me/{agent.username}"
                ),
            ]
            for agent in agents_tg_chats
        ]
        keyboard.append(build_back_button("back_to_choose_gov"))
        keyboard.append(back_to_user_home_page_button[0])
        await update.callback_query.edit_message_text(
            text=f"وكلاء محافظة <b>{syrian_govs_en_ar[gov]}</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


back_to_choose_gov = show_trusted_agents

show_trusted_agents_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            show_trusted_agents,
            "^trusted agents$",
        )
    ],
    states={
        CHOOSE_GOV: [
            CallbackQueryHandler(
                choose_gov,
                govs_pattern,
            ),
        ]
    },
    fallbacks=[
        CallbackQueryHandler(back_to_choose_gov, "^back_to_choose_gov$"),
        back_to_user_home_page_handler,
        start_command,
    ],
)
