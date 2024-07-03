from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ContextTypes,
)

from telegram.error import (
    RetryAfter,
)

from DB import DB
import asyncio
import os

from constants import *

from common.common import apply_ex_rate


worker_type_dict = {
    "daily": {
        "approved_work": "approved_withdraws_day",
        "percentage": "workers_reward_withdraw_percentage",
        "role": "withdraws",
        "day_week": "اليوم",
    },
    "weekly": {
        "approved_work": "approved_deposits_week",
        "percentage": "workers_reward_percentage",
        "role": "deposits",
        "day_week": "الأسبوع",
    },
}


def stringify_manager_reward_report(worker, updated_worker, amount, reward_type):
    role = worker_type_dict[reward_type]["role"]
    manager_text = (
        f"تم تحديث رصيد المكافآت عن مجموع مبالغ الطلبات الناجحة للموظف:\n\n"
        f"id: <code>{worker['id']}</code>\n"
        f"name: <b>{worker['name']}</b>\n"
        f"username: {'@' + worker['username'] if worker['username'] else '<b>لا يوجد</b>'}\n\n"
        f"مجموع المكافآت السابق: <b>{worker[f'{reward_type}_rewards_balance']}</b>\n"
        f"قيمة المكافأة: <b>{amount}</b>\n"
        f"مجموع المكافآت الحالي: <b>{updated_worker[f'{reward_type}_rewards_balance']}</b>\n"
        f"عدد الطلبات حتى الآن: <b>{updated_worker[f'approved_{role}_num']}</b>\n"
        f"مجموع المبالغ حتى الآن: <b>{updated_worker[f'approved_{role}']}</b>\n"
        f"مجموع المبالغ هذا {worker_type_dict[reward_type]['day_week']}: <b>{worker[f'approved_{role}_{reward_type}']}</b>"
    )
    return manager_text


def stringify_worker_reward_report(worker, updated_worker, amount, reward_type):
    role = worker_type_dict[reward_type]["role"]
    worker_text = (
        "تم تحديث رصيد مكافآتك عن مجموع قيم الطلبات التي تمت الموافقة عليها\n"
        f"مجموع مكافآتك السابق: <b>{worker[f'{reward_type}_rewards_balance']}</b>\n"
        f"قيمة المكافأة: <b>{amount}</b>\n"
        f"مجموع مكافآتك الحالي: <b>{updated_worker[f'{reward_type}_rewards_balance']}</b>\n"
        f"عدد الطلبات حتى الآن: <b>{updated_worker[f'approved_{role}_num']}</b>\n"
        f"مجموع المبالغ حتى الآن: <b>{updated_worker[f'approved_{role}']}</b>\n"
        f"مجموع المبالغ هذا {worker_type_dict[reward_type]['day_week']}: <b>{worker[f'approved_{role}_{reward_type}']}</b>\n"
    )
    return worker_text


async def reward_worker(context: ContextTypes.DEFAULT_TYPE):
    worker_type = context.job.name.split("_")[0]
    workers = DB.get_all_workers(payments=worker_type == "daily")
    for worker in workers:
        if worker[worker_type_dict[worker_type]["approved_work"]] == 0:
            continue

        amount = (
            worker[worker_type_dict[worker_type]["approved_work"]]
            * context.bot_data["data"][worker_type_dict[worker_type]["percentage"]]
            / 100
        )
        if worker_type == "daily":
            await DB.daily_reward_worker(
                worker_id=worker["id"], amount=amount, method=worker["method"]
            )
        else:
            await DB.weekly_reward_worker(worker_id=worker["id"], amount=amount)

        updated_worker = DB.get_worker(
            worker_id=worker["id"],
            method=worker["method"] if worker_type == "daily" else None,
        )

        worker_text = stringify_worker_reward_report(
            worker, updated_worker, amount, worker_type
        )
        try:
            await context.bot.send_message(
                chat_id=worker["id"],
                text=worker_text,
            )
        except:
            pass

        manager_text = stringify_manager_reward_report(
            worker, updated_worker, amount, worker_type
        )

        try:
            await context.bot.send_message(
                chat_id=context.bot_data["data"]["worker_gifts_group"],
                text=manager_text,
            )
        except RetryAfter as r:
            await asyncio.sleep(r.retry_after)
            await context.bot.send_message(
                chat_id=context.bot_data["data"]["worker_gifts_group"],
                text=manager_text,
            )


async def check_deposit(context: ContextTypes.DEFAULT_TYPE):
    check_deposit_jobs_dict = {
        "1_deposit_check": 240,
        "2_deposit_check": 240,
        "3_deposit_check": 840,
        "4_deposit_check": 5040,
    }
    serial = int(context.job.data)
    d_order = DB.get_one_order(
        "deposit",
        serial=serial,
    )
    ref_present = DB.get_ref_number(
        number=d_order["ref_number"],
        method=d_order["method"],
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
        text = stringify_order(
            amount="لا يوجد",
            account_number=d_order["acc_number"],
            method=d_order["method"],
            serial=d_order["serial"],
            ref_num=d_order["ref_number"],
        )
        text_list = text.split("\n")
        text_list.insert(0, "تم رفض الطلب❌")
        text = "\n".join(text_list) + f"\n\nالسبب:\n<b>{reason}</b>"

        message = await context.bot.send_message(
            chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
            text=text,
        )
        await DB.set_deposit_not_arrived(
            reason=reason, serial=serial, archive_message_ids=message.id
        )


async def send_order_to_process(d_order, ref_info, context: ContextTypes.DEFAULT_TYPE):
    amount, ex_rate = apply_ex_rate(
        d_order["method"],
        ref_info["amount"],
        "deposit",
        context,
    )

    message = await context.bot.send_message(
        chat_id=context.bot_data["data"]["deposit_after_check_group"],
        text=stringify_order(
            amount=amount,
            account_number=d_order["acc_number"],
            method=d_order["method"],
            serial=d_order["serial"],
            ref_num=ref_info["number"],
        ),
        reply_markup=InlineKeyboardMarkup.from_button(
            InlineKeyboardButton(
                text="قبول الطلب✅",
                callback_data=f"verify_deposit_order_{d_order['serial']}",
            )
        ),
    )
    await DB.send_order(
        order_type="deposit",
        pending_process_message_id=message.id,
        serial=d_order["serial"],
        ref_info=ref_info,
        group_id=context.bot_data["data"]["deposit_after_check_group"],
        ex_rate=ex_rate,
    )


def stringify_order(
    amount: float, serial: int, method: str, account_number: int, ref_num: str, *args
):
    return (
        "إيداع جديد:\n"
        f"رقم العملية: {ref_num}\n"
        f"المبلغ: <code>{amount}</code>\n"
        f"رقم الحساب: <code>{account_number}</code>\n\n"
        f"وسيلة الدفع: <code>{method}</code>\n\n"
        f"Serial: <code>{serial}</code>\n\n"
        "تنبيه: اضغط على رقم الحساب والمبلغ لنسخها كما هي في الرسالة تفادياً للخطأ.\n\n"
        "ملاحظة: تأكد من تطابق المبلغ في الرسالة مع الذي في لقطة الشاشة لأن ما سيضاف في حالة التأكيد هو الذي في الرسالة."
    )
