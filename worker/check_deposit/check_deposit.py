from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    ContextTypes,
)

from common.common import (
    apply_ex_rate,
    notify_workers,
    format_amount,
)
from models import RefNumber, DepositOrder, DepositAgent

import os
import asyncio

check_deposit_lock = asyncio.Lock()


async def check_deposit(context: ContextTypes.DEFAULT_TYPE):
    await check_deposit_lock.acquire()  # We're using the lock because we're checking deposit on storing ref too, so there's a possible conflict.

    serial = int(context.job.data)
    d_order = DepositOrder.get_one_order(
        serial=serial,
    )
    if d_order and d_order.state != "pending":
        check_deposit_lock.release()
        return

    check_deposit_jobs_dict = {
        "1_deposit_check": 240,
        "2_deposit_check": 300,
        "3_deposit_check": 600,
        "4_deposit_check": 600,
    }
    ref_present = RefNumber.get_ref_number(
        number=d_order.ref_number,
        method=d_order.method,
    )
    if ref_present:
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
        reason = "لم يجد البوت رقم عملية الدفع المرتبط بهذا الطلب"
        await context.bot.send_message(
            chat_id=context.job.user_id,
            text=(
                f"{reason}\n\n"
                f"الرقم التسلسلي للطلب: {serial}\n"
                f"نوع الطلب: إيداع\n\n"
                "عليك التحقق وإعادة الطلب مرة أخرى، سيتم التحقق بشكل دوري."
            ),
        )
        text = (
            "تم رفض الطلب❌\n"
            + stringify_order(
                amount=0,
                account_number=d_order.acc_number,
                method=d_order.method,
                serial=d_order.serial,
                ref_num=d_order.ref_number,
                wal=d_order.deposit_wallet,
            )
            + f"\n\nالسبب:\n<b>{reason}</b>"
        )

        await context.bot.send_message(
            chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
            text=text,
        )
        await DepositOrder.decline_order(
            reason=reason,
            serial=serial,
        )
    check_deposit_lock.release()


async def send_order_to_process(
    d_order: DepositOrder, ref_info: RefNumber, context: ContextTypes.DEFAULT_TYPE
):
    amount, ex_rate = apply_ex_rate(
        method=d_order.method,
        amount=ref_info.amount,
        order_type="deposit",
        context=context,
    )
    order_text = stringify_order(
        amount=amount,
        account_number=d_order.acc_number,
        method=d_order.method,
        serial=d_order.serial,
        ref_num=ref_info.number,
        wal=d_order.deposit_wallet,
    )

    message = await context.bot.send_message(
        chat_id=context.bot_data["data"]["deposit_after_check_group"],
        text=order_text,
        reply_markup=InlineKeyboardMarkup.from_button(
            InlineKeyboardButton(
                text="قبول الطلب✅",
                callback_data=f"verify_deposit_order_{d_order.serial}",
            )
        ),
    )

    await DepositOrder.send_order(
        pending_process_message_id=message.id,
        serial=d_order.serial,
        ref_info=ref_info,
        group_id=context.bot_data["data"]["deposit_after_check_group"],
        ex_rate=ex_rate,
    )
    workers = DepositAgent.get_workers()
    asyncio.create_task(
        notify_workers(
            context=context,
            workers=workers,
            text=f"انتباه تم استلام إيداع جديد رقم العملية <code>{ref_info.number}</code> 🚨",
        )
    )


def stringify_order(
    amount: float,
    serial: int,
    method: str,
    account_number: int,
    ref_num: str,
    wal:str,
    *args,
):
    return (
        "إيداع جديد:\n"
        f"رقم العملية: <code>{ref_num}</code>\n"
        f"المبلغ 💵: <code>{amount if amount else 'لا يوجد بعد'}</code>\n"
        f"رقم الحساب: <code>{account_number}</code>\n\n"
        f"وسيلة الدفع: <code>{method}</code>\n"
        f"المحفظة: <code>{wal}</code>\n\n"
        f"Serial: <code>{serial}</code>\n\n"
        "تنبيه: اضغط على رقم الحساب والمبلغ لنسخها كما هي في الرسالة تفادياً للخطأ."
    )
