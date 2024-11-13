from telegram.ext import ContextTypes
from telegram.error import RetryAfter, BadRequest
import models
from common.constants import *
from common.stringifies import (
    worker_type_dict,
    stringify_manager_reward_report,
    stringify_reward_report,
    stringify_daily_order_stats,
    stringify_daily_wallet_stats,
)
from common.common import notify_workers, format_amount
from common.functions import send_deposit_without_check, find_min_hourly_sum

import asyncio
import os
from datetime import datetime, timedelta
import random
import pytz


async def reward_worker(context: ContextTypes.DEFAULT_TYPE):
    worker_type = context.job.name.split("_")[0]
    model: models.DepositAgent | models.PaymentAgent = worker_type_dict[worker_type][
        "model"
    ]
    workers: list[models.PaymentAgent] | list[models.DepositAgent] = model.get_workers()
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
        await models.Wallet.update_wallets(
            method=method,
            option="balance",
            value=0,
        )
    agents = models.DepositAgent.get_workers()
    asyncio.create_task(notify_workers(context, agents, "الرجاء إخلاء جميع المحافظ 🚨"))


async def process_orders_for_ghafla_offer(context: ContextTypes.DEFAULT_TYPE):
    time_window = random.randint(7, 15)
    group_by_interval = "GROUP BY interval"

    distinct_user_id_orders = models.DepositOrder.get_orders(
        ghafla_offer={
            "time_window": time_window,
            "group_by": "",
            "agg": "",
        }
    )
    amounts_sum = models.DepositOrder.get_orders(
        ghafla_offer={
            "time_window": time_window,
            "group_by": group_by_interval,
            "agg": "SUM(amount),",
        }
    )

    selected_date = None
    for amount_sum in amounts_sum:
        if amount_sum[1] <= 50000:
            selected_date = amount_sum[0]
            break

    if not selected_date:
        return

    already_won_orders: list[models.DepositOrder] = models.DepositOrder.get_orders(
        method=GHAFLA_OFFER, today=True
    )
    already_won_users = list(
        map(
            lambda x: x.user_id,
            already_won_orders,
        )
    )

    selected_serials = [
        order[1] for order in distinct_user_id_orders if order[0] == selected_date
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

    base_group_text = (
        f"عرض الغفلة <b>500%</b> 🔥\n\n"
        f"من ال: <b>{start_time}</b>\n"
        f"حتى ال: <b>{end_time}</b>\n\n"
        "الرابحون:\n\n"
    )
    group_text = base_group_text
    for serial in selected_serials:
        order = models.DepositOrder.get_one_order(serial=serial)
        if order.user_id in already_won_users:
            continue
        factor = 4
        amount = order.amount * factor
        try:
            user = await context.bot.get_chat(chat_id=order.user_id)
            name = "@" + user.username if user.username else f"<b>{user.full_name}</b>"
        except BadRequest:
            user = models.User.get_user(user_id=order.user_id)
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

        await models.Offer.add(serial=serial, factor=factor, offer_name=GHAFLA_OFFER)
    if group_text != base_group_text:
        await context.bot.send_message(
            chat_id=int(os.getenv("CHANNEL_ID")),
            text=group_text,
            message_thread_id=int(os.getenv("GHAFLA_OFFER_TOPIC_ID")),
        )
        for serial in selected_serials:
            order = models.DepositOrder.get_one_order(serial=serial)
            await context.bot.send_message(
                chat_id=order.user_id,
                text=group_text,
            )


async def process_orders_for_lucky_hour_offer(context: ContextTypes.DEFAULT_TYPE):
    team_names = ["مدريد", "برشلونة", "ميلان", "ليفربول", "باريس"]

    order_type_dict = {
        models.WithdrawOrder: "السحب",
        models.DepositOrder: "الإيداع"
    }

    withdraw_orders = models.WithdrawOrder.get_orders(lucky_hour_offer=True, states=["approved", "sent"])
    deposit_orders = models.DepositOrder.get_orders(lucky_hour_offer=True, states=["approved"])
    min_withdraws = find_min_hourly_sum(withdraw_orders)
    min_deposits = find_min_hourly_sum(deposit_orders)

    if min_withdraws["min_sum"] == 0 and min_deposits["min_sum"] == 0:
        return
    elif min_withdraws["min_sum"] == 0:
        min_sum = min_deposits["min_sum"]
    elif min_deposits["min_sum"] == 0:
        min_sum = min_withdraws["min_sum"]
    else:
        min_sum = min(min_withdraws["min_sum"], min_deposits["min_sum"])

    min_orders = min_withdraws if min_withdraws["min_sum"] == min_sum else min_deposits
    percentage = context.bot_data["lucky_hour_amount"] * 100 / min_orders["min_sum"]
    start_time = (
        (
            datetime.fromisoformat(str(min_orders["orders"][0].order_date))
            + timedelta(hours=3)
        )
        .time()
        .strftime(r"%I:%M %p")
    )
    end_time = (
        (
            datetime.fromisoformat(str(min_orders["orders"][0].order_date))
            + timedelta(hours=4)
        )
        .time()
        .strftime(r"%I:%M %p")
    )
    offer_text = (
        "خليك بساعة الحظ، الحظ بده رضاك\n"
        "ما تروح وتسيبها، يمكن تربح معاك\n\n"
        f"<b>ساعة {random.choice(team_names)} {format_amount(percentage)}%</b> 🔥\n\n"
        f"لطلبات {order_type_dict[type(min_orders["orders"][0])]}\n"
        f"من ال: <b>{start_time}</b>\n"
        f"حتى ال: <b>{end_time}</b>\n\n"
        "الرابحون:\n\n"
    )
    for order in min_orders["orders"]:
        order: models.DepositOrder | models.WithdrawOrder = order
        amount = order.amount * percentage / 100
        try:
            user = await context.bot.get_chat(chat_id=order.user_id)
            name = "@" + user.username if user.username else f"<b>{user.full_name}</b>"
        except BadRequest:
            user = models.User.get_user(user_id=order.user_id)
            name = "@" + user.username if user.username else f"<b>{user.name}</b>"
        offer_text += (
            f"الاسم:\n{name}\n" f"رقم الحساب: <code>{order.acc_number}</code>\n\n"
        )
        await send_deposit_without_check(
            context=context,
            acc_number=order.acc_number,
            user_id=order.user_id,
            amount=amount,
            method=LUCKY_HOUR_OFFER,
        )
        if not context.bot_data.get("total_lucky_hour_offer", False):
            context.bot_data["total_lucky_hour_offer"] = amount
        else:
            context.bot_data["total_lucky_hour_offer"] += amount

        await models.Offer.add(
            serial=order.serial, factor=percentage, offer_name=LUCKY_HOUR_OFFER
        )

    offer_text += "<b>ملاحظة: نظراً للعدد الكبير تم الاكتفاء بذكر أسماء أبرز المستفيدين</b>",
    for order in min_orders["orders"]:
        await context.bot.send_message(
            chat_id=order.user_id,
            text=offer_text,
        )
    await context.bot.send_message(
        chat_id=int(os.getenv("CHANNEL_ID")),
        text=offer_text,
        message_thread_id=int(os.getenv("GHAFLA_OFFER_TOPIC_ID")),
    )


async def schedule_offers_jobs(context: ContextTypes.DEFAULT_TYPE):
    tz = pytz.timezone("Asia/Damascus")
    today = datetime.now(tz=tz)
    schedule_ghafla_offer_jobs(context=context, today=today, tz=tz)
    schedule_lucky_hour_jobs(context=context, today=today, tz=tz)
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


def schedule_ghafla_offer_jobs(
    context: ContextTypes.DEFAULT_TYPE,
    today: datetime,
    tz,
):
    ghafla_offer_base_job_name = "process_orders_for_ghafla_offer"
    job_hours_dict = {
        0: random.randint(0, 2),
        1: random.randint(3, 5),
        2: random.randint(6, 8),
        3: random.randint(9, 11),
        4: random.randint(12, 14),
        5: random.randint(15, 17),
        6: random.randint(18, 20),
        7: random.randint(21, 23),
    }
    for i in job_hours_dict:
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
        context.job_queue.run_once(
            process_orders_for_ghafla_offer,
            when=when,
            name=ghafla_offer_base_job_name + f"_{i}",
            job_kwargs={
                "id": ghafla_offer_base_job_name + f"_{i}",
                "misfire_grace_time": None,
                "coalesce": True,
                "replace_existing": True,
            },
        )


def schedule_lucky_hour_jobs(
    context: ContextTypes.DEFAULT_TYPE,
    today: datetime,
    tz,
):
    lucky_hour_offer_base_job_name = "process_orders_for_lucky_hour_offer"
    job_hours_dict = {
        0: random.randint(12, 14),
        1: random.randint(15, 17),
        2: random.randint(18, 20),
        3: random.randint(21, 23),
        4: random.randint(0, 2),
    }
    for i in job_hours_dict:
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
        context.job_queue.run_once(
            process_orders_for_lucky_hour_offer,
            when=when,
            name=lucky_hour_offer_base_job_name + f"_{i}",
            job_kwargs={
                "id": lucky_hour_offer_base_job_name + f"_{i}",
                "misfire_grace_time": None,
                "coalesce": True,
                "replace_existing": True,
            },
        )


async def send_daily_stats(context: ContextTypes.DEFAULT_TYPE):
    withdraw_stats = models.WithdrawOrder.calc_daily_stats()
    deposit_stats = models.DepositOrder.calc_daily_stats()

    wallets_stats_text = ""
    for method in PAYMENT_METHODS_LIST:
        wallets_stats = models.Wallet.get_wallets(method=method)
        if not wallets_stats:
            continue

        wallets_stats_text += (
            stringify_daily_wallet_stats(method=method, stats=wallets_stats) + "\n\n"
        )

    await context.bot.send_message(
        chat_id=int(os.getenv("OWNER_ID")),
        text=(
            stringify_daily_order_stats("إيداعات", stats=deposit_stats)
            + "\n\n"
            + stringify_daily_order_stats("سحوبات", stats=withdraw_stats)
            + "\n\n"
            + wallets_stats_text
        ),
    )
