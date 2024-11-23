from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
import functools
from common.constants import *
from models import Account, User, TrustedAgent
from common.common import parent_to_child_models_mapper


def check_if_user_agent_decorator(func):
    @functools.wraps(func)
    async def wrapper(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
    ):
        agent = TrustedAgent.get_workers(user_id=update.effective_user.id)
        if not agent:
            await update.callback_query.answer(
                "قم بتسجيل الدخول أولاً",
                show_alert=True,
            )
            return
        return await func(update, context, *args, **kwargs)

    return wrapper


def check_user_pending_orders_decorator(func):
    @functools.wraps(func)
    async def wrapper(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
    ):
        try:
            order_type = update.callback_query.data
            states = ["pending", "processing", "checking", "sent"]
            if order_type == "withdraw":
                states = ["pending", "checking"]
            order = parent_to_child_models_mapper[order_type].get_one_order(
                user_id=update.effective_user.id,
                states=states,
            )
            if order:
                await update.callback_query.answer(
                    text=(
                        "لديك طلب قيد التنفيذ بالفعل ❗️\n" f"رقم الطلب: {order.serial}"
                    ),
                    show_alert=True,
                )
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
            if not context.bot_data["user_calls"][
                update.callback_query.data
            ] and update.effective_user.id not in [
                6190159711,
            ]:
                await update.callback_query.answer(
                    "هذه الخدمة متوقفة حالياً ❗️",
                    show_alert=True,
                )
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
