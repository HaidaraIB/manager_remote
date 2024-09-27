from telegram.ext import ContextTypes
from telegram.error import RetryAfter
from models import PaymentAgent, DepositAgent, Wallet, DepositOrder
from common.constants import *
from common.stringifies import (
    worker_type_dict,
    stringify_manager_reward_report,
    stringify_reward_report,
)
from common.common import notify_workers
from common.functions import send_deposit_without_check

import asyncio
import os
from datetime import datetime, timedelta
import random
import pytz


async def reward_worker(context: ContextTypes.DEFAULT_TYPE):
    worker_type = context.job.name.split("_")[0]
    model: DepositAgent | PaymentAgent = worker_type_dict[worker_type]["model"]
    workers: list[PaymentAgent] | list[DepositAgent] = model.get_workers()
    for worker in workers:
        approved_work = getattr(
            worker, worker_type_dict[worker_type]["approved_work"], None
        )
        if not approved_work:
            continue

        amount = float(
            approved_work
            * context.bot_data[worker_type_dict[worker_type]["percentage"]]
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


async def remind_agent_to_clear_wallets(context: ContextTypes.DEFAULT_TYPE):
    context.bot_data["create_account_deposit"] = context.bot_data[
        "create_account_deposit_pin"
    ]
    for method in PAYMENT_METHODS_LIST + ["طلبات الوكيل"]:
        await Wallet.update_wallets(
            method=method,
            option="balance",
            value=0,
        )
    agents = DepositAgent.get_workers()
    asyncio.create_task(notify_workers(context, agents, "الرجاء إخلاء جميع المحافظ 🚨"))


async def process_orders_for_ghafla_offer(context: ContextTypes.DEFAULT_TYPE):
    time_window = 15
    group_by_user = "user_id"
    group_by_interval = "interval"

    distinct_user_id_orders = DepositOrder.get_orders(
        time_window=time_window, group_by=group_by_user
    )
    amounts_sum = DepositOrder.get_orders(
        time_window=time_window, group_by=group_by_interval
    )

    selected_date = None
    for amount_sum in amounts_sum:
        if amount_sum[1] <= 100000:
            selected_date = amount_sum[0]
            break

    if not selected_date:
        return

    selected_serials = [
        order[2] for order in distinct_user_id_orders if order[0] == selected_date
    ]

    start_time = datetime.fromisoformat(str(selected_date)).time().strftime("%H:%M")
    end_time = (
        (datetime.fromisoformat(str(selected_date)) + timedelta(minutes=time_window))
        .time()
        .strftime("%H:%M")
    )

    group_text = f"المستفيدين من عرض الغفلة <b>500%</b> من الساعة <b>{start_time}</b> حتى الساعة <b>{end_time}</b>:\n"
    for serial in selected_serials:
        order = DepositOrder.get_one_order(serial=serial)
        group_text += f"<code>{order.acc_number}</code>\n"
        await send_deposit_without_check(
            context=context,
            acc_number=order.acc_number,
            user_id=order.user_id,
            amount=order.amount * 4,
            method=GHAFLA_OFFER,
        )

    await context.bot.send_message(
        chat_id=int(os.getenv("CHANNEL_ID")),
        text=group_text,
        message_thread_id=int(os.getenv("GHAFLA_OFFER_TOPIC_ID")),
    )


async def schedule_ghafla_offer_jobs(context: ContextTypes.DEFAULT_TYPE):
    tz = pytz.timezone("Asia/Damascus")
    today = datetime.now(tz=tz)
    ghafla_offer_base_job_name = "process_orders_for_ghafla_offer"
    job_names_dict = {
        0: f"{ghafla_offer_base_job_name}_morning",
        1: f"{ghafla_offer_base_job_name}_noon",
        2: f"{ghafla_offer_base_job_name}_after_noon",
        3: f"{ghafla_offer_base_job_name}_evening",
    }
    job_hours_dict = {
        0: random.randint(7, 9),
        1: random.randint(11, 13),
        2: random.randint(15, 17),
        3: random.randint(19, 21),
    }
    for i in range(4):
        context.job_queue.run_once(
            process_orders_for_ghafla_offer,
            when=datetime(
                today.year,
                today.month,
                today.day,
                job_hours_dict[i],
                tzinfo=tz,
            ),
            name=job_names_dict[i],
            job_kwargs={
                "id": job_names_dict[i],
                "misfire_grace_time": None,
                "coalesce": True,
                "replace_existing": True,
            },
        )
