from telegram.ext import ContextTypes
from telegram.error import RetryAfter
from models import PaymentAgent, DepositAgent
from common.common import format_amount
from common.constants import *
import asyncio
from common.stringifies import (
    worker_type_dict,
    stringify_manager_reward_report,
    stringify_reward_report,
)


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
            updated_worker = model.get_workers(
                worker_id=worker.id,
                method=worker.method,
            )
        else:
            await model.weekly_reward_worker(
                worker_id=worker.id,
                amount=amount,
            )
            updated_worker = model.get_workers(
                worker_id=worker.id,
                is_point=worker.is_point,
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
