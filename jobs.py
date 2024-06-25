from telegram.ext import (
    ContextTypes,
)

from telegram.constants import (
    ParseMode,
)

from telegram.error import (
    RetryAfter,
)

from DB import DB
import asyncio


async def weekly_reward_worker(context: ContextTypes.DEFAULT_TYPE):
    workers = DB.get_workers()
    for worker in workers:

        if worker['approved_deposits_week'] == 0:
            continue

        amount = worker['approved_deposits_week'] * context.bot_data["data"]["workers_reward_percentage"] / 100
        await DB.weekly_reward_worker(worker_id=worker['id'], amount=amount)
        updated_worker = DB.get_worker(worker_id=worker['id'])

        worker_text = f"""تم تحديث مكافآتك الأسبوعية عن مجموع مبالغ الإيداع التي تمت الموافقة عليها
مجموع مكافآتك الأسبوعية السابق: <b>{worker['weekly_rewards_balance']}</b>
قيمة المكافأة: <b>{amount}</b>
مجموع مكافآتك الأسبوعية الحالي: <b>{updated_worker['weekly_rewards_balance']}</b>
عدد الإيداعات حتى الآن: <b>{updated_worker['approved_deposits_num']}</b>
مجموع مبالغ الإيداعات حتى الآن: <b>{updated_worker['approved_deposits']}</b>
مجموع مبالغ الإيداعات هذا الأسبوع: <b>{worker['approved_deposits_week']}</b>
"""
        try:
            await context.bot.send_message(
                chat_id=worker['id'], text=worker_text,
            )
        except:
            pass

        manager_text = f"""تم تحديث المكافآت الأسبوعية عن مجموع مبالغ الإيداع الناجحة للموظف:

id: <code>{worker['id']}</code>
name: <b>{worker['name']}</b>
username: {'@' + worker['username'] if worker['username'] else '<b>لا يوجد</b>'}

مجموع المكافآت الأسبوعية السابق: <b>{worker['weekly_rewards_balance']}</b>
قيمة المكافأة: <b>{amount}</b>
مجموع المكافآت الأسبوعية الحالي: <b>{updated_worker['weekly_rewards_balance']}</b>
عدد الإيداعات حتى الآن: <b>{updated_worker['approved_deposits_num']}</b>
مجموع مبالغ الإيداعات حتى الآن: <b>{updated_worker['approved_deposits']}</b>
مجموع مبالغ الإيداعات هذا الأسبوع: <b>{worker['approved_deposits_week']}</b>
"""
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

        if worker['approved_withdraws_day'] == 0:
            continue

        amount = (
            worker['approved_withdraws_day']
            * context.bot_data["data"]["workers_reward_withdraw_percentage"]
            / 100
        )
        await DB.daily_reward_worker(worker_id=worker['id'], amount=amount, method=worker['method'])
        updated_worker = DB.get_worker(worker_id=worker['id'], method=worker['method'])

        worker_text = f"""تم تحديث مكافآتك اليومية عن مجموع مبالغ الإيداع التي تمت الموافقة عليها
مجموع مكافآتك اليومية السابق: <b>{worker['daily_rewards_balance']}</b>
قيمة المكافأة: <b>{amount}</b>
مجموع مكافآتك اليومية الحالي: <b>{updated_worker['daily_rewards_balance']}</b>
عدد السحوبات حتى الآن: <b>{updated_worker['approved_withdraws_num']}</b>
مجموع مبالغ السحوبات حتى الآن: <b>{updated_worker['approved_withdraws']}</b>
مجموع مبالغ السحوبات هذا الأسبوع: <b>{worker['approved_withdraws_day']}</b>
"""
        try:
            await context.bot.send_message(
                chat_id=worker['id'], text=worker_text,
            )
        except:
            pass

        manager_text = f"""تم تحديث المكافآت اليومية عن مجموع مبالغ الإيداع الناجحة للموظف:

id: <code>{worker['id']}</code>
name: <b>{worker['name']}</b>
username: {'@' + worker['username'] if worker['username'] else '<b>لا يوجد</b>'}

مجموع مكافآتك اليومية السابق: <b>{worker['daily_rewards_balance']}</b>
قيمة المكافأة: <b>{amount}</b>
مجموع مكافآتك اليومية الحالي: <b>{updated_worker['daily_rewards_balance']}</b>
عدد السحوبات حتى الآن: <b>{updated_worker['approved_withdraws_num']}</b>
مجموع مبالغ السحوبات حتى الآن: <b>{updated_worker['approved_withdraws']}</b>
مجموع مبالغ السحوبات هذا اليوم: <b>{worker['approved_withdraws_day']}</b>
"""
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
