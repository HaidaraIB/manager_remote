from telegram import Update, Chat, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from worker.check_deposit.check_deposit import check_deposit
from common.back_to_home_page import back_to_user_home_page_button
from common.stringifies import stringify_deposit_order
from common.force_join import check_if_user_member_decorator
from common.constants import *
from common.common import (
    notify_workers,
    build_methods_keyboard,
    build_back_button,
    send_to_photos_archive,
)
from common.decorators import (
    check_user_pending_orders_decorator,
    check_user_call_on_or_off_decorator,
    check_if_user_present_decorator,
    check_if_user_created_account_from_bot_decorator,
)

import models
import asyncio

ACCOUNT_DEPOSIT, DEPOSIT_METHOD = range(2)


@check_user_pending_orders_decorator
@check_user_call_on_or_off_decorator
@check_if_user_present_decorator
@check_if_user_member_decorator
@check_if_user_created_account_from_bot_decorator
async def make_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        accounts = models.Account.get_user_accounts(user_id=update.effective_user.id)
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
    ref_num: str = "",
    agent_id: int = 0,
    gov: str = "",
):
    ref_present = models.RefNumber.get_ref_number(
        number=ref_num,
        method=method,
    )
    order_present = models.DepositOrder.get_one_order(ref_num=ref_num, method=method)
    if (ref_present and ref_present.order_serial != -1) or (
        order_present and order_present.state == "approved"
    ):
        return False

    serial = await models.DepositOrder.add_deposit_order(
        user_id=user_id,
        group_id=target_group,
        method=method,
        acc_number=acc_number,
        deposit_wallet=context.bot_data["data"][f"{method}_number"],
        amount=0,
        ref_number=ref_num,
        agent_id=agent_id,
        gov=gov,
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

    message = await context.bot.send_message(
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

    await models.DepositOrder.add_message_ids(
        serial=serial,
        pending_check_message_id=message.id,
    )

    workers = models.DepositAgent.get_workers()
    asyncio.create_task(
        notify_workers(
            context=context,
            workers=workers,
            text=f"انتباه يوجد طلب قيد التحقق رقم عملية <code>{ref_num}</code> 🚨",
        )
    )
    return True


async def send_to_check_bemo_deposit(
    update: Update, context: ContextTypes.DEFAULT_TYPE, is_point_deposit=False
):
    user_id = update.effective_user.id
    photo = update.message.photo[-1]

    if is_point_deposit:
        ref_number = context.user_data["point_deposit_ref_num"]
        deposit_wallet = context.bot_data["data"]["طلبات الوكيل_number"]
        amount = context.user_data["point_deposit_amount"]
        gov = context.user_data["point_deposit_point"]
        agent = models.TrustedAgent.get_workers(user_id=user_id, gov=gov)
    else:
        amount = context.user_data["deposit_amount"]
        acc_number = context.user_data["account_deposit"]
        method = context.user_data["deposit_method"]
        deposit_wallet = context.bot_data["data"][f"{method}_number"]

    target_group = context.bot_data["data"]["deposit_orders_group"]

    serial = await models.DepositOrder.add_deposit_order(
        user_id=user_id,
        group_id=target_group,
        method=SYRCASH if is_point_deposit else method,
        acc_number=acc_number if not is_point_deposit else None,
        deposit_wallet=deposit_wallet,
        amount=amount,
        ref_number=ref_number if is_point_deposit else None,
        agent_id=user_id if is_point_deposit else None,
        gov=agent.gov if is_point_deposit else None,
    )

    caption = stringify_deposit_order(
        amount=amount,
        serial=serial,
        method=SYRCASH if is_point_deposit else method,
        wal=deposit_wallet,
        ref_num=ref_number if is_point_deposit else None,
        account_number=acc_number if not is_point_deposit else None,
        workplace_id=agent.team_cash_workplace_id if is_point_deposit else None,
    )
    markup = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton(
            text="التحقق ☑️", callback_data=f"check_deposit_order_{serial}"
        )
    )

    message = await context.bot.send_photo(
        chat_id=target_group,
        photo=photo,
        caption=caption,
        reply_markup=markup,
    )
    await send_to_photos_archive(
        context=context,
        photo=photo,
        serial=serial,
        order_type="deposit",
    )

    await models.DepositOrder.add_message_ids(
        serial=serial,
        pending_check_message_id=message.id,
    )

    workers = models.DepositAgent.get_workers(is_point=is_point_deposit)
    asyncio.create_task(
        notify_workers(
            context=context,
            workers=workers,
            text=f"انتباه يوجد طلب تحقق إيداع جديد 🚨",
        )
    )
    workers = models.Checker.get_workers(
        check_what="deposit",
        method=POINT_DEPOSIT if is_point_deposit else method,
    )
    asyncio.create_task(
        notify_workers(
            context=context,
            workers=workers,
            text=f"انتباه يوجد طلب تحقق إيداع جديد 🚨",
        )
    )