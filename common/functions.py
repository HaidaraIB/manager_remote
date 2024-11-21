from telegram import InlineKeyboardButton, InlineKeyboardMarkup, error
from telegram.ext import ContextTypes
from common.stringifies import stringify_deposit_order, order_settings_dict
from common.common import notify_workers, format_amount
import asyncio
import models
from datetime import timedelta
import os


async def send_deposit_without_check(
    context: ContextTypes.DEFAULT_TYPE,
    acc_number: int,
    user_id: int,
    amount: float,
    method: str,
    from_withdraw_serial: int = 0,
):
    target_group = context.bot_data["data"]["deposit_orders_group"]
    serial = await models.DepositOrder.add_deposit_order(
        user_id=user_id,
        group_id=target_group,
        method=method,
        amount=amount,
        acc_number=acc_number,
        from_withdraw_serial=from_withdraw_serial,
    )
    order_text = stringify_deposit_order(
        amount=amount,
        serial=serial,
        method=method,
        account_number=acc_number,
    )

    timed_out = True
    while timed_out:
        try:
            message = await context.bot.send_message(
                chat_id=context.bot_data["data"]["deposit_after_check_group"],
                text=order_text,
                reply_markup=InlineKeyboardMarkup.from_button(
                    InlineKeyboardButton(
                        text="قبول الطلب ✅",
                        callback_data=f"verify_deposit_order_{serial}",
                    )
                ),
                read_timeout=20,
                write_timeout=20,
                connect_timeout=20,
            )
            timed_out = False
        except error.TimedOut:
            pass

    await models.DepositOrder.send_order(
        pending_process_message_id=message.id,
        serial=serial,
        group_id=context.bot_data["data"]["deposit_after_check_group"],
        ex_rate=1,
    )
    workers = models.DepositAgent.get_workers(is_point=False)
    asyncio.create_task(
        notify_workers(
            context=context,
            workers=workers,
            text=f"انتباه تم استلام إيداع {method} جديد 🚨",
        )
    )
    return amount


def find_min_hourly_sum(
    orders: list[models.DepositOrder | models.WithdrawOrder],
) -> dict:
    min_sum = float("inf")
    current_sum = 0
    window_orders: list[models.DepositOrder | models.WithdrawOrder] = []
    min_orders: list[models.DepositOrder | models.WithdrawOrder] = []

    for order in orders:
        # Add the current order to the window
        window_orders.append(order)
        current_sum += order.amount

        # Remove orders outside the 1-hour window
        while window_orders and window_orders[
            0
        ].order_date < order.order_date - timedelta(hours=1):
            removed_order = window_orders.pop(0)
            current_sum -= removed_order.amount

        # Update min_sum and min_window_orders if the current sum is smaller
        if current_sum < min_sum:
            min_sum = current_sum
            min_orders = window_orders.copy()

    return {
        "min_sum": min_sum,
        "orders": min_orders,
    }


async def end_offer(context: ContextTypes.DEFAULT_TYPE, order_type: str):
    p = context.bot_data[f"{order_type}_offer_percentage"]
    msg_id = context.bot_data[f"{order_type}_offer_msg_id"]

    context.bot_data[f"{order_type}_offer_total_stats"] = 0
    context.bot_data[f"{order_type}_offer_total"] = 0
    context.bot_data[f"{order_type}_offer_percentage"] = 0
    context.bot_data[f"{order_type}_offer_hour"] = 0
    context.bot_data[f"{order_type}_offer_min_amount"] = 0
    context.bot_data[f"{order_type}_offer_max_amount"] = 0
    context.bot_data[f"{order_type}_offer_msg_id"] = 0

    await context.bot.send_message(
        chat_id=int(os.getenv("CHANNEL_ID")),
        text=(
            f"انتهى عرض ال{order_settings_dict[order_type]['t']} <b>{format_amount(p)}%</b> 🏁"
        ),
        message_thread_id=int(os.getenv("GHAFLA_OFFER_TOPIC_ID")),
        reply_to_message_id=msg_id,
    )


def check_offer(context: ContextTypes.DEFAULT_TYPE, amount: float, order_type: str):
    p = context.bot_data[f"{order_type}_offer_percentage"]
    if (
        p != 0
        and amount <= context.bot_data[f"{order_type}_offer_max_amount"]
        and amount >= context.bot_data[f"{order_type}_offer_min_amount"]
    ):
        gift = amount * (p / 100)
        if gift < context.bot_data[f"{order_type}_offer_total"]:
            context.bot_data[f"{order_type}_offer_total"] -= gift
            context.bot_data[f"{order_type}_offer_total_stats"] += gift
        elif gift == context.bot_data[f"{order_type}_offer_total"]:
            context.bot_data[f"{order_type}_offer_total"] = -1  # to end offer
            context.bot_data[f"{order_type}_offer_total_stats"] += gift
        else:
            context.bot_data[f"{order_type}_offer_total"] = -1  # to end offer
            p = 0
    return p
