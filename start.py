from telegram import (
    Update,
    Chat,
    BotCommandScopeChat,
    ReplyKeyboardRemove,
)

from telegram.ext import (
    CommandHandler,
    ContextTypes,
    Application,
    ConversationHandler,
)

from database import User

from common.common import (
    build_user_keyboard,
    build_admin_keyboard,
    build_worker_keyboard,
    check_hidden_keyboard,
)

from common.force_join import check_if_user_member

from custom_filters import Admin, Worker, DepositAgent


async def inits(app: Application):
    if not app.bot_data.get("data", False):
        app.bot_data["data"] = {
            "deposit_gift_percentage": 1,
            "workers_reward_percentage": 1,
            "workers_reward_withdraw_percentage": 1,
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


async def set_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    st_cmd = ("start", "start command")
    if Worker().filter(update):
        commands = [("worker", "worker command"), st_cmd]
    elif Admin().filter(update):
        commands = [("admin", "admin command"), st_cmd]
    else:
        commands = [st_cmd]
    await context.bot.set_my_commands(
        commands=commands, scope=BotCommandScopeChat(chat_id=update.effective_chat.id)
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        await set_commands(update, context)
        old_user = User.get_user(user_id=update.effective_user.id)
        if not old_user:
            new_user = update.effective_user
            await User.add_new_user(
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
            text="القائمة الرئيسية🔝",
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


worker_command = CommandHandler(command="worker", callback=worker)
admin_command = CommandHandler(command="admin", callback=admin)
start_command = CommandHandler(command="start", callback=start)
