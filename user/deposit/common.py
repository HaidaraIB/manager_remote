from telegram import Update, Chat, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from models import RefNumber, DepositOrder, DepositAgent
from worker.check_deposit.check_deposit import check_deposit
from common.common import notify_workers, build_methods_keyboard, build_back_button
from common.back_to_home_page import back_to_user_home_page_button
from common.stringifies import stringify_deposit_order
from common.decorators import (
    check_user_pending_orders_decorator,
    check_user_call_on_or_off_decorator,
    check_if_user_present_decorator,
    check_if_user_created_account_from_bot_decorator,
)
from common.force_join import check_if_user_member_decorator
from models import Account
import asyncio


ACCOUNT_DEPOSIT, DEPOSIT_METHOD = range(2)


@check_user_pending_orders_decorator
@check_user_call_on_or_off_decorator
@check_if_user_present_decorator
@check_if_user_member_decorator
@check_if_user_created_account_from_bot_decorator
async def make_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        accounts = Account.get_user_accounts(user_id=update.effective_user.id)
        accounts_keyboard = [
            InlineKeyboardButton(
                text=a.acc_num,
                callback_data=str(a.acc_num),
            )
            for a in accounts
        ]
        keybaord = [
            accounts_keyboard,
            back_to_user_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text="اختر حساباً من حساباتك المسجلة لدينا",
            reply_markup=InlineKeyboardMarkup(keybaord),
        )
        return ACCOUNT_DEPOSIT


async def account_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        if not update.callback_query.data.startswith("back"):
            context.user_data["account_deposit"] = int(update.callback_query.data)
        deposit_methods = build_methods_keyboard()
        deposit_methods.append(build_back_button("back_to_account_number_deposit"))
        deposit_methods.append(back_to_user_home_page_button[0])
        await update.callback_query.edit_message_text(
            text="اختر وسيلة الدفع 💳",
            reply_markup=InlineKeyboardMarkup(deposit_methods),
        )
        return DEPOSIT_METHOD


back_to_account_deposit = make_deposit


async def send_to_check_deposit(
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
    method: str,
    acc_number: str,
    target_group: int,
    ref_num: str = None,
    agent_id: int = None,
):
    ref_present = RefNumber.get_ref_number(
        number=ref_num,
        method=method,
    )
    order_present = DepositOrder.get_one_order(ref_num=ref_num, method=method)
    if (ref_present and ref_present.order_serial != -1) or (
        order_present and order_present.state == "approved"
    ):
        return False

    serial = await DepositOrder.add_deposit_order(
        user_id=user_id,
        group_id=target_group,
        method=method,
        acc_number=acc_number,
        deposit_wallet=context.bot_data["data"][f"{method}_number"],
        amount=0,
        ref_number=ref_num,
        agent_id=agent_id if agent_id else 0,
    )

    context.job_queue.run_once(
        callback=check_deposit,
        user_id=user_id,
        when=60,
        data=serial,
        name="1_deposit_check",
        job_kwargs={
            "misfire_grace_time": None,
            "coalesce": True,
        },
    )

    await context.bot.send_message(
        chat_id=target_group,
        text=stringify_deposit_order(
            amount=0,
            serial=serial,
            method=method,
            account_number=acc_number,
            wal=context.bot_data["data"][f"{method}_number"],
            ref_num=ref_num,
        ),
    )

    workers = DepositAgent.get_workers()
    asyncio.create_task(
        notify_workers(
            context=context,
            workers=workers,
            text=f"انتباه يوجد طلب قيد التحقق رقم عملية <code>{ref_num}</code> 🚨",
        )
    )
    return True
