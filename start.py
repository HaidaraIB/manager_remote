from telegram import Update, Chat, BotCommandScopeChat, ReplyKeyboardRemove
from telegram.ext import CommandHandler, ContextTypes, Application, ConversationHandler
import models
from common.common import (
    build_user_keyboard,
    build_admin_keyboard,
    build_worker_keyboard,
    build_agent_keyboard,
    check_hidden_keyboard,
)
from common.force_join import check_if_user_member
from custom_filters import Admin, Worker, DepositAgent, Agent
from common.constants import *


async def inits(app: Application):
    pass  # Fill this when you need to run a code only once and then clear it.


async def set_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    st_cmd = ("start", "start command")
    commands = set()
    if update.effective_chat.type == Chat.PRIVATE:
        if Worker().filter(update):
            commands.add(st_cmd)
            commands.add(("worker", "worker command"))

        if Admin().filter(update):
            commands.add(st_cmd)
            commands.add(("admin", "admin command"))

        if Agent().filter(update):
            commands.add(st_cmd)
            commands.add(("agent", "agent command"))
    elif update.effective_chat.type in [Chat.SUPERGROUP, Chat.GROUP]:
        if (
            update.effective_chat.id
            == context.bot_data["data"]["accounts_orders_group"]
        ):
            commands.add(("count", "count accounts"))
    await context.bot.set_my_commands(
        commands=commands, scope=BotCommandScopeChat(chat_id=update.effective_chat.id)
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        await set_commands(update, context)
        old_user = models.User.get_user(user_id=update.effective_user.id)
        if not old_user:
            new_user = update.effective_user
            await models.User.add_new_user(
                user_id=new_user.id,
                username=new_user.username,
                name=new_user.full_name,
            )

        member = await check_if_user_member(update=update, context=context)
        if not member:
            return

        await update.message.reply_text(
            text="أهلاً بك...",
            reply_markup=ReplyKeyboardRemove(),
        )
        await update.message.reply_text(
            text=HOME_PAGE_TEXT,
            reply_markup=build_user_keyboard(),
        )
        return ConversationHandler.END


async def worker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Worker().filter(update):
        await update.message.reply_text(
            text="أهلاً بك...",
            reply_markup=build_worker_keyboard(
                deposit_agent=DepositAgent().filter(update)
            ),
        )
        return ConversationHandler.END


async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        await update.message.reply_text(
            text="أهلاً بك...",
            reply_markup=check_hidden_keyboard(context),
        )
        await update.message.reply_text(
            text="تعمل الآن كآدمن🕹",
            reply_markup=build_admin_keyboard(),
        )
        return ConversationHandler.END


async def agent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        if update.callback_query:
            await update.callback_query.delete_message()
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text=AGENT_COMMAND_TEXT,
            reply_markup=build_agent_keyboard(),
        )
        return ConversationHandler.END


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    "".error()


worker_command = CommandHandler(command="worker", callback=worker)
admin_command = CommandHandler(command="admin", callback=admin)
start_command = CommandHandler(command="start", callback=start)
agent_command = CommandHandler(command="agent", callback=agent)
error_command = CommandHandler(command="error", callback=error)
