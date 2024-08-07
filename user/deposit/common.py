from telegram.ext import ContextTypes
from models import RefNumber, DepositOrder, DepositAgent
from worker.check_deposit.check_deposit import check_deposit, stringify_order
from common.common import notify_workers
import asyncio


async def send_to_check_deposit(
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
    ref_num: str,
    method: str,
    acc_number: str,
    target_group: int,
    agent_id:int = None,
):
    ref_present = RefNumber.get_ref_number(
        number=ref_num,
        method=method,
    )
    order_present = DepositOrder.get_one_order(ref_num=ref_num, method=method)
    if (ref_present and ref_present.order_serial != -1) or (
        order_present and order_present.state == "approved"
    ):
        return False

    serial = await DepositOrder.add_deposit_order(
        user_id=user_id,
        method=method,
        acc_number=acc_number,
        ref_number=ref_num,
        deposit_wallet=context.bot_data['data'][f'{method}_number'],
        agent_id=agent_id if agent_id else 0,
    )

    context.job_queue.run_once(
        callback=check_deposit,
        user_id=user_id,
        when=60,
        data=serial,
        name="1_deposit_check",
        job_kwargs={
            "misfire_grace_time": None,
            "coalesce": True,
        },
    )

    await context.bot.send_message(
        chat_id=target_group,
        text=stringify_order(
            amount=0,
            account_number=acc_number,
            method=method,
            serial=serial,
            ref_num=ref_num,
            wal=context.bot_data['data'][f'{method}_number']
        ),
    )

    workers = DepositAgent.get_workers()
    asyncio.create_task(
        notify_workers(
            context=context,
            workers=workers,
            text=f"انتباه يوجد طلب قيد التحقق رقم عملية <code>{ref_num}</code> 🚨",
        )
    )
    return True