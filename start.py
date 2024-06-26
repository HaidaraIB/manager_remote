from telegram import (
    Update,
    Chat,
)

from telegram.ext import (
    CommandHandler,
    ContextTypes,
    Application,
    ConversationHandler,
    CallbackQueryHandler,
)

from telegram.constants import (
    ParseMode,
    ChatMemberStatus,
)

import os
from DB import DB

from common.common import (
    build_user_keyboard,
    build_admin_keyboard,
    build_worker_keyboard,
    check_if_user_member,
    check_hidden_keyboard,
)

from custom_filters.Admin import Admin


async def inits(app: Application):
    if not app.bot_data.get("data", False):
        app.bot_data["data"] = {
            "deposit_gift_percentage": 1,
            "workers_reward_percentage": 1,
            "workers_reward_percentage_withdraw": 2,
            "user_calls": {
                "withdraw": True,
                "deposit": True,
                "buy_usdt": True,
                "create_account": True,
                "make_complaint": True,
            },
        }
    if not app.bot_data.get("suspended_workers", False):
        app.bot_data["suspended_workers"] = set()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        old_user = DB.get_user(user_id=update.effective_user.id)
        if not old_user:
            new_user = update.effective_user
            await DB.add_new_user(
                user_id=new_user.id,
                username=new_user.username,
                name=new_user.full_name,
            )

        member = await check_if_user_member(update=update, context=context)
        if not member:
            return

        text = "أهلاً بك..."
        keyboard = build_user_keyboard()

        await update.message.reply_text(
            text=text, reply_markup=keyboard
        )
        return ConversationHandler.END


async def worker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        d_agent = DB.get_deposit_agent(user_id=update.effective_user.id)
        p_agent = DB.get_payment_agent(user_id=update.effective_user.id)
        checker = DB.get_checker(user_id=update.effective_user.id)
        if p_agent or d_agent or checker:
            text = "أهلاً بك..."
            keyboard = build_worker_keyboard()
            await update.message.reply_text(
                text=text, reply_markup=keyboard
            )
            return ConversationHandler.END


async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        await update.message.reply_text(
            text="أهلاً بك...",
            reply_markup=check_hidden_keyboard(context),
        )
        text = "تعمل الآن كآدمن🕹"
        keyboard = build_admin_keyboard()
        await update.message.reply_text(
            text=text, reply_markup=keyboard
        )
        return ConversationHandler.END


async def check_joined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_memeber = await context.bot.get_chat_member(
        chat_id=int(os.getenv("CHANNEL_ID")), user_id=update.effective_user.id
    )
    if chat_memeber.status == ChatMemberStatus.LEFT:
        await update.callback_query.answer(
            text="قم بالاشتراك بالقناة أولاً", show_alert=True
        )
        return

    text = "أهلاً بك..."
    keyboard = build_user_keyboard()
    await update.callback_query.edit_message_text(
        text=text, reply_markup=keyboard
    )


worker_command = CommandHandler(command="worker", callback=worker)
admin_command = CommandHandler(command="admin", callback=admin)
start_command = CommandHandler(command="start", callback=start)

check_joined_handler = CallbackQueryHandler(
    callback=check_joined, pattern="^check joined$"
)
