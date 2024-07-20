from telegram.ext import (
    ContextTypes,
)

from telegram.error import (
    RetryAfter,
)

import asyncio
from models import PaymentAgent, DepositAgent
from constants import *
from common.common import format_amount

worker_type_dict = {
    "daily": {
        "approved_work": "approved_withdraws_day",
        "percentage": "workers_reward_withdraw_percentage",
        "role": "withdraws",
        "day_week": {
            "ar": "اليوم",
            "en": "day",
        },
        "model": PaymentAgent,
    },
    "weekly": {
        "approved_work": "approved_deposits_week",
        "percentage": "workers_reward_percentage",
        "role": "deposits",
        "day_week": {"ar": "الأسبوع", "en": "week"},
        "model": DepositAgent,
    },
}


def stringify_manager_reward_report(
    worker: DepositAgent | PaymentAgent,
    updated_worker: DepositAgent | PaymentAgent,
    amount: float,
    reward_type: str,
):
    manager_text = (
        f"تم تحديث رصيد المكافآت عن مجموع مبالغ الطلبات الناجحة للموظف:\n\n"
        f"id: <code>{worker.id}</code>\n"
        f"name: <b>{worker.name}</b>\n"
        f"username: {'@' + worker.username if worker.username else '<b>لا يوجد</b>'}\n\n"
    )
    return manager_text + stringify_reward_report(
        worker=worker,
        updated_worker=updated_worker,
        amount=amount,
        reward_type=reward_type,
    )


def stringify_reward_report(
    worker: DepositAgent | PaymentAgent,
    updated_worker: DepositAgent | PaymentAgent,
    amount: float,
    reward_type: str,
):
    role = worker_type_dict[reward_type]["role"]
    balance = updated_worker.__getattribute__(f'approved_{role}')
    partial_balance = worker.__getattribute__(f'approved_{role}_{worker_type_dict[reward_type]['day_week']['en']}')
    prev_rewards_balance = worker.__getattribute__(f'{reward_type}_rewards_balance')
    rewards_balance = updated_worker.__getattribute__(f'{reward_type}_rewards_balance')
    orders_num = updated_worker.__getattribute__(f'approved_{role}_num')
    work_type = worker_type_dict[reward_type]['day_week']['ar']
    
    worker_text = (
        f"الوظيفة: {f'سحب {updated_worker.method}' if role == 'withdraws' else 'تنفيذ إيداع'}\n"
        f"مجموع المكافآت السابق: <b>{format_amount(prev_rewards_balance)}</b>\n"
        f"قيمة المكافأة: <b>{format_amount(amount)}</b>\n"
        f"مجموع المكافآت الحالي: <b>{format_amount(rewards_balance)}</b>\n"
        f"عدد الطلبات حتى الآن: <b>{orders_num}</b>\n"
        f"مجموع المبالغ حتى الآن: <b>{format_amount(balance)}</b>\n"
        f"مجموع المبالغ هذا {work_type}: <b>{format_amount(partial_balance)}</b>"
    )
    return worker_text


async def reward_worker(context: ContextTypes.DEFAULT_TYPE):
    worker_type = context.job.name.split("_")[0]
    model: DepositAgent | PaymentAgent = worker_type_dict[worker_type]["model"]
    workers: list[PaymentAgent] | list[DepositAgent] = model.get_workers()
    for worker in workers:
        approved_work = worker.__getattribute__(
            worker_type_dict[worker_type]["approved_work"]
        )
        if approved_work == 0:
            continue

        amount = float(
            approved_work
            * context.bot_data["data"][worker_type_dict[worker_type]["percentage"]]
            / 100
        )
        if worker_type == "daily":
            await model.daily_reward_worker(
                worker_id=worker.id,
                amount=amount,
                method=worker.method,
            )
        else:
            await model.weekly_reward_worker(
                worker_id=worker.id,
                amount=amount,
            )

        updated_worker = model.get_workers(
            worker_id=worker.id,
            method=worker.method if worker_type == "daily" else None,
        )

        worker_text = (
            "تم تحديث رصيد مكافآتك عن مجموع قيم الطلبات التي تمت الموافقة عليها\n"
            + stringify_reward_report(worker, updated_worker, amount, worker_type)
        )
        try:
            await context.bot.send_message(
                chat_id=worker.id,
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
