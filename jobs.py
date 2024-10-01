from telegram.ext import ContextTypes
from telegram.error import RetryAfter, BadRequest
from models import PaymentAgent, DepositAgent, Wallet, DepositOrder, GhaflaOffer, User
from common.constants import *
from common.stringifies import (
    worker_type_dict,
    stringify_manager_reward_report,
    stringify_reward_report,
)
from common.common import notify_workers, format_amount, format_datetime
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
    start_time = (
        (datetime.fromisoformat(str(selected_date)) + timedelta(hours=3))
        .time()
        .strftime(r"%I:%M %p")
    )
    end_time = (
        (
            datetime.fromisoformat(str(selected_date))
            + timedelta(hours=3, minutes=time_window)
        )
        .time()
        .strftime(r"%I:%M %p")
    )

    group_text = (
        f"عرض الغفلة <b>500%</b> 🔥\n\n"
        f"من الساعة: <b>{start_time}</b>\n"
        f"حتى الساعة: <b>{end_time}</b>\n\n"
        "الرابحون:\n\n"
    )
    for serial in selected_serials:
        order = DepositOrder.get_one_order(serial=serial)
        factor = 4
        amount = order.amount * factor
        try:
            user = await context.bot.get_chat(chat_id=order.user_id)
            name = "@" + user.username if user.username else f"<b>{user.full_name}</b>"
        except BadRequest:
            user = User.get_user(user_id=order.user_id)
            name = "@" + user.username if user.username else f"<b>{user.name}</b>"
        group_text += (
            f"الاسم:\n{name}\n" f"رقم الحساب: <code>{order.acc_number}</code>\n\n"
        )
        await send_deposit_without_check(
            context=context,
            acc_number=order.acc_number,
            user_id=order.user_id,
            amount=amount,
            method=GHAFLA_OFFER,
        )
        if not context.bot_data.get("total_ghafla_offer", False):
            context.bot_data["total_ghafla_offer"] = amount
        else:
            context.bot_data["total_ghafla_offer"] += amount

        await GhaflaOffer.add(serial=serial, factor=factor)

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
    dev_id = int(os.getenv("DEV_ID"))
    await context.bot.send_message(
        chat_id=dev_id,
        text=f"أوقات عرض الغفلة:",
    )
    for i in range(4):
        when = datetime(
            year=today.year,
            month=today.month,
            day=today.day,
            hour=job_hours_dict[i],
            minute=0,
            second=0,
            microsecond=0,
            tzinfo=tz,
        )
        await context.bot.send_message(
            chat_id=dev_id,
            text=format_datetime(when),
        )
        context.job_queue.run_once(
            process_orders_for_ghafla_offer,
            when=when,
            name=job_names_dict[i],
            job_kwargs={
                "id": job_names_dict[i],
                "misfire_grace_time": None,
                "coalesce": True,
                "replace_existing": True,
            },
        )

    if not context.bot_data.get("total_ghafla_offer", False):
        context.bot_data["total_ghafla_offer"] = 0
    else:
        create_account_deposits = 0
        if context.bot_data["create_account_deposit"] < 0:
            create_account_deposits = context.bot_data[
                "create_account_deposit_pin"
            ] + abs(context.bot_data["create_account_deposit"])

        elif context.bot_data["create_account_deposit"] == 0:
            create_account_deposits = context.bot_data["create_account_deposit_pin"]

        else:
            create_account_deposits = (
                context.bot_data["create_account_deposit_pin"]
                - context.bot_data["create_account_deposit"]
            )
        await context.bot.send_message(
            chat_id=int(os.getenv("OWNER_ID")),
            text=(
                f"عرض الغفلة اليوم: <b>{format_amount(context.bot_data['total_ghafla_offer'])}</b> ل.س\n\n"
                f"إنشاء الحسابات اليوم: <b>{format_amount(create_account_deposits)}</b> ل.س"
            ),
        )
        context.bot_data["create_account_deposit"] = context.bot_data[
            "create_account_deposit_pin"
        ]
        context.bot_data["total_ghafla_offer"] = 0
