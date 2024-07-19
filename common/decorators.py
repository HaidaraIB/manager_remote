from telegram import (
    Update,
)

from telegram.ext import (
    ContextTypes,
    ConversationHandler,
)
import functools
from constants import *
from database import Account, User


def check_if_user_created_account_from_bot_decorator(func):
    @functools.wraps(func)
    async def wrapper(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
    ):
        accounts = Account.get_user_accounts(user_id=update.effective_user.id)
        if not accounts:
            await update.callback_query.answer(
                "قم بإنشاء حساب موثق عن طريق البوت أولاً ❗️",
                show_alert=True,
            )
            return ConversationHandler.END
        return await func(update, context, *args, **kwargs)

    return wrapper


def check_if_user_present_decorator(func):
    @functools.wraps(func)
    async def wrapper(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
    ):
        user = User.get_user(user_id=update.effective_user.id)
        if not user:
            new_user = update.effective_user
            await User.add_new_user(
                user_id=new_user.id,
                username=new_user.username,
                name=new_user.full_name,
            )
        return await func(update, context, *args, **kwargs)

    return wrapper
