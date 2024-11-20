from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from common.common import apply_ex_rate, notify_workers
from common.stringifies import stringify_deposit_order, create_order_user_info_line
from common.constants import *
from common.functions import end_offer, check_offer
import models
import os
import asyncio

check_deposit_lock = asyncio.Lock()


async def check_deposit(context: ContextTypes.DEFAULT_TYPE):
    try:
        await check_deposit_lock.acquire()  # We're using the lock because we're checking deposit on storing ref too, so there's a possible conflict.

        serial = int(context.job.data)
        d_order = models.DepositOrder.get_one_order(
            serial=serial,
        )
        if d_order and d_order.state != "pending":
            return

        check_deposit_jobs_dict = {
            "1_deposit_check": 240,
            "2_deposit_check": 300,
            "3_deposit_check": 600,
            "4_deposit_check": 600,
        }
        ref_present = models.RefNumber.get_ref_number(
            number=d_order.ref_number,
            method=d_order.method,
        )
        if ref_present and ref_present.order_serial == -1:
            await send_order_to_process(
                d_order=d_order,
                ref_info=ref_present,
                context=context,
            )
        elif context.job.name in check_deposit_jobs_dict:
            next_job_num = int(context.job.name.split("_")[0]) + 1
            context.job_queue.run_once(
                callback=check_deposit,
                user_id=context.job.user_id,
                when=check_deposit_jobs_dict[context.job.name],
                data=serial,
                name=f"{next_job_num}_deposit_check",
                job_kwargs={
                    "misfire_grace_time": None,
                    "coalesce": True,
                },
            )
        else:
            if ref_present and ref_present.order_serial == -1:
                reason = "رقم عملية مكرر"
                sugg = ""
            else:
                reason = "لم يجد البوت رقم عملية الدفع المرتبط بهذا الطلب"
                sugg = "إن كنت تظن أن هذا خطأ، أعد تقديم الطلب وحسب."
            try:
                await context.bot.send_message(
                    chat_id=context.job.user_id,
                    text=(
                        f"{reason}\n\n"
                        f"الرقم التسلسلي للطلب: {serial}\n"
                        f"نوع الطلب: إيداع\n\n" + sugg
                    ),
                )
            except:
                pass
            order_user_info_line = await create_order_user_info_line(
                user_id=d_order.user_id, context=context
            )
            text = (
                DECLINE_TEXT
                + "\n"
                + stringify_deposit_order(
                    amount=d_order.amount,
                    serial=d_order.serial,
                    method=d_order.method,
                    account_number=d_order.acc_number,
                    wal=d_order.deposit_wallet,
                    ref_num=d_order.ref_number,
                )
                + order_user_info_line
                + f"السبب:\n<b>{reason}</b>"
            )

            await context.bot.send_message(
                chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
                text=text,
            )
            await models.DepositOrder.decline_order(
                reason=reason,
                serial=serial,
            )
    finally:
        check_deposit_lock.release()


async def send_order_to_process(
    d_order: models.DepositOrder,
    ref_info: models.RefNumber,
    context: ContextTypes.DEFAULT_TYPE,
):
    amount, ex_rate = apply_ex_rate(
        method=d_order.method,
        amount=ref_info.amount,
        order_type="deposit",
        context=context,
    )
    offer = check_offer(context, amount, "deposit")
    total_amount = amount
    if offer:
        total_amount += amount * (offer / 100)
        offer_id = await models.Offer.add(
            serial=d_order.serial,
            factor=offer,
            offer_name=DEPOSIT_OFFER,
            min_amount=context.bot_data[f"deposit_offer_min_amount"],
            max_amount=context.bot_data[f"deposit_offer_max_amount"],
        )
    if context.bot_data["deposit_offer_total"] == -1:
        await end_offer(context, "deposit")
    order_text = stringify_deposit_order(
        amount=total_amount,
        order_amount=amount,
        serial=d_order.serial,
        method=d_order.method,
        account_number=d_order.acc_number,
        wal=d_order.deposit_wallet,
        ref_num=ref_info.number,
        offer=offer,
    )

    message = await context.bot.send_message(
        chat_id=context.bot_data["data"]["deposit_after_check_group"],
        text=order_text,
        reply_markup=InlineKeyboardMarkup.from_button(
            InlineKeyboardButton(
                text="قبول الطلب ✅",
                callback_data=f"verify_deposit_order_{d_order.serial}",
            )
        ),
    )

    await models.DepositOrder.send_order(
        pending_process_message_id=message.id,
        serial=d_order.serial,
        ref_info=ref_info,
        group_id=context.bot_data["data"]["deposit_after_check_group"],
        ex_rate=ex_rate,
        offer=offer_id,
    )
    workers = models.DepositAgent.get_workers(is_point=False)
    asyncio.create_task(
        notify_workers(
            context=context,
            workers=workers,
            text=f"انتباه تم استلام إيداع جديد رقم العملية <code>{ref_info.number}</code> 🚨",
        )
    )
