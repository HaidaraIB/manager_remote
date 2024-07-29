from telegram import (
    Update,
)

from telegram.ext import (
    ContextTypes,
    ConversationHandler,
)
import functools
from common.constants import *
from models import (
    Account,
    User,
)
from common.common import parent_to_child_models_mapper


def check_user_pending_orders_decorator(func):
    @functools.wraps(func)
    async def wrapper(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
    ):
        try:
            if parent_to_child_models_mapper[
                update.callback_query.data
            ].check_user_pending_orders(
                user_id=update.effective_user.id,
            ):
                await update.callback_query.answer("لديك طلب قيد التنفيذ بالفعل ❗️ - You have an order under process ❗️")
                return ConversationHandler.END
        except KeyError:
            pass
        return await func(update, context, *args, **kwargs)

    return wrapper


def check_user_call_on_or_off_decorator(func):
    @functools.wraps(func)
    async def wrapper(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
    ):
        try:
            if not context.bot_data["data"]["user_calls"][update.callback_query.data]:
                await update.callback_query.answer("هذه الخدمة متوقفة حالياً ❗️ - This freature is off ❗️")
                return ConversationHandler.END
        except KeyError:
            pass
        return await func(update, context, *args, **kwargs)

    return wrapper


def check_if_user_created_account_from_bot_decorator(func):
    @functools.wraps(func)
    async def wrapper(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
    ):
        accounts = Account.get_user_accounts(user_id=update.effective_user.id)
        if not accounts:
            await update.callback_query.answer(
                "قم بإنشاء حساب موثق عن طريق البوت أولاً  ❗️ - Create an account via the bot first ❗️",
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
