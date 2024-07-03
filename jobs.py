from telegram.ext import (
    ContextTypes,
)

from telegram.error import (
    RetryAfter,
)

from DB import DB
import asyncio

from constants import *

worker_type_dict = {
    "daily": {
        "approved_work": "approved_withdraws_day",
        "percentage": "workers_reward_withdraw_percentage",
        "role": "withdraws",
        "day_week": {
            "ar": "اليوم",
            "en": "day",
        },
    },
    "weekly": {
        "approved_work": "approved_deposits_week",
        "percentage": "workers_reward_percentage",
        "role": "deposits",
        "day_week": {"ar": "الأسبوع", "en": "week"},
    },
}


def stringify_manager_reward_report(worker, updated_worker, amount, reward_type):
    role = worker_type_dict[reward_type]["role"]

    manager_text = (
        f"تم تحديث رصيد المكافآت عن مجموع مبالغ الطلبات الناجحة للموظف:\n\n"
        f"id: <code>{worker['id']}</code>\n"
        f"name: <b>{worker['name']}</b>\n"
        f"username: {'@' + worker['username'] if worker['username'] else '<b>لا يوجد</b>'}\n\n"
        f"الوظيفة: {f'سحب {updated_worker['method']}' if role == 'withdraws' else "تنفيذ إيداع"}\n"
        f"مجموع المكافآت السابق: <b>{worker[f'{reward_type}_rewards_balance']}</b>\n"
        f"قيمة المكافأة: <b>{amount}</b>\n"
        f"مجموع المكافآت الحالي: <b>{updated_worker[f'{reward_type}_rewards_balance']}</b>\n"
        f"عدد الطلبات حتى الآن: <b>{updated_worker[f'approved_{role}_num']}</b>\n"
        f"مجموع المبالغ حتى الآن: <b>{updated_worker[f'approved_{role}']}</b>\n"
        f"مجموع المبالغ هذا {worker_type_dict[reward_type]['day_week']['ar']}: <b>{worker[f'approved_{role}_{worker_type_dict[reward_type]['day_week']['en']}']}</b>"
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
        f"مجموع المبالغ هذا {worker_type_dict[reward_type]['day_week']['ar']}: <b>{worker[f'approved_{role}_{worker_type_dict[reward_type]['day_week']['en']}']}</b>\n"
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