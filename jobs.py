from telegram.ext import (
    ContextTypes,
)

from telegram.error import (
    RetryAfter,
)

from DB import DB
import asyncio

day_week_en_to_ar_dict = {"day": "اليوم", "week": "الأسبوع"}


def stringify_manager_reward_report(worker, updated_worker, amount, reward_type, role):
    manager_text = (
        f"تم تحديث رصيد المكافآت عن مجموع مبالغ الطلبات الناجحة للموظف:\n\n"
        f"id: <code>{worker['id']}</code>\n"
        f"name: <b>{worker['name']}</b>\n"
        f"username: {'@' + worker['username'] if worker['username'] else '<b>لا يوجد</b>'}\n\n"
        f"مجموع المكافآت السابق: <b>{worker[f'{reward_type}ly_rewards_balance']}</b>\n"
        f"قيمة المكافأة: <b>{amount}</b>\n"
        f"مجموع المكافآت الحالي: <b>{updated_worker[f'{reward_type}ly_rewards_balance']}</b>\n"
        f"عدد الطلبات حتى الآن: <b>{updated_worker[f'approved_{role}_num']}</b>\n"
        f"مجموع المبالغ حتى الآن: <b>{updated_worker[f'approved_{role}']}</b>\n"
        f"مجموع المبالغ هذا {day_week_en_to_ar_dict[reward_type]}: <b>{worker[f'approved_{role}_{reward_type}']}</b>"
    )
    return manager_text


def stringify_worker_reward_report(worker, updated_worker, amount, reward_type, role):
    worker_text = (
        "تم تحديث رصيد مكافآتك عن مجموع قيم الطلبات التي تمت الموافقة عليها\n"
        f"مجموع مكافآتك السابق: <b>{worker[f'{reward_type}ly_rewards_balance']}</b>\n"
        f"قيمة المكافأة: <b>{amount}</b>\n"
        f"مجموع مكافآتك الحالي: <b>{updated_worker[f'{reward_type}ly_rewards_balance']}</b>\n"
        f"عدد الطلبات حتى الآن: <b>{updated_worker[f'approved_{role}_num']}</b>\n"
        f"مجموع المبالغ حتى الآن: <b>{updated_worker[f'approved_{role}']}</b>\n"
        f"مجموع المبالغ هذا {day_week_en_to_ar_dict[reward_type]}: <b>{worker[f'approved_{role}_{reward_type}']}</b>\n"
    )
    return worker_text


async def weekly_reward_worker(context: ContextTypes.DEFAULT_TYPE):
    workers = DB.get_workers()
    for worker in workers:

        if worker["approved_deposits_week"] == 0:
            continue

        amount = (
            worker["approved_deposits_week"]
            * context.bot_data["data"]["workers_reward_percentage"]
            / 100
        )
        await DB.weekly_reward_worker(worker_id=worker["id"], amount=amount)
        updated_worker = DB.get_worker(worker_id=worker["id"])

        worker_text = stringify_worker_reward_report(
            worker, updated_worker, amount, "week", "deposits"
        )

        try:
            await context.bot.send_message(
                chat_id=worker["id"],
                text=worker_text,
            )
        except:
            pass

        manager_text = stringify_manager_reward_report(
            worker, updated_worker, amount, "week", "deposits"
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


async def daily_reward_worker(context: ContextTypes.DEFAULT_TYPE):
    workers = DB.get_all_workers(payments=True)
    for worker in workers:

        if worker["approved_withdraws_day"] == 0:
            continue

        amount = (
            worker["approved_withdraws_day"]
            * context.bot_data["data"]["workers_reward_withdraw_percentage"]
            / 100
        )
        await DB.daily_reward_worker(
            worker_id=worker["id"], amount=amount, method=worker["method"]
        )
        updated_worker = DB.get_worker(worker_id=worker["id"], method=worker["method"])

        worker_text = stringify_worker_reward_report(
            worker, updated_worker, amount, "day", "withdraws"
        )
        try:
            await context.bot.send_message(
                chat_id=worker["id"],
                text=worker_text,
            )
        except:
            pass

        manager_text = stringify_manager_reward_report(
            worker, updated_worker, amount, "day", "withdraws"
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
