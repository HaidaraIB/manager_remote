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

import models

from common.common import (
    build_user_keyboard,
    build_admin_keyboard,
    build_worker_keyboard,
    check_hidden_keyboard,
)

from common.force_join import check_if_user_member
from custom_filters import Admin, Worker, DepositAgent
from common.constants import *

import os


async def inits(app: Application):
    await models.Admin.add_new_admin(admin_id=os.getenv("OWNER_ID"))
    await models.PaymentMethod.init_payment_methods()
    if not app.bot_data.get("data", None):
        app.bot_data['data'] = {}


async def set_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    st_cmd = ("start", "start command")
    commands = [st_cmd]
    if Worker().filter(update):
        commands.append(("worker", "worker command"))
    if Admin().filter(update):
        commands.append(("admin", "admin command"))
    await context.bot.set_my_commands(
        commands=commands, scope=BotCommandScopeChat(chat_id=update.effective_chat.id)
    )


async def send_ads(update: Update):
    await update.message.reply_text(
        text=(
            "عند استخدامك زر إنشاء حساب موثق تستفيد من استرداد أسبوعي 20%.\n"
            "By using the Verified Account Creation button, you benefit from a 20% weekly cashback."
        ),
    )
    await update.message.reply_text(
        text=(
            "عند استخدامك المزايا التي يقدمها البوت لايوجد رسوم على عمليات الإيداع والسحب.\n"
            "When you use the features provided by the bot, there are no fees for deposit and withdrawal transactions."
        ),
    )
    await update.message.reply_text(
        text=(
            "تمتع بالمرونة في عمليات السحب حيث يمكنك استخدام وسيلة مختلفة عن تلك التي استخدمتها في الإيداع.\n"
            "Enjoy flexibility in withdrawal transactions; you can use a different method than the one used for deposits."
        ),
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
        await send_ads(update)
        await update.message.reply_text(
            text="أهلاً بك... - Welcome...",
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


worker_command = CommandHandler(command="worker", callback=worker)
admin_command = CommandHandler(command="admin", callback=admin)
start_command = CommandHandler(command="start", callback=start)
