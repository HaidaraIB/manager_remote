from telegram import InlineKeyboardButton
from PyroClientSingleton import PyroClientSingleton
from common.common import parent_to_child_models_mapper
from common.constants import *
import models

orders_dict = {
    "withdraw": "سحب",
    "deposit": "إيداع",
    "busdt": "شراء usdt",
}


def build_payment_agent_keyboard(agent: list[models.PaymentAgent]):
    keyboard: list[list] = []
    for i in range(0, len(agent), 2):
        row = []
        row.append(
            InlineKeyboardButton(
                text=f"دفع {agent[i].method}",
                callback_data=f"request {agent[i].method}",
            )
        )
        if i + 1 < len(agent):
            row.append(
                InlineKeyboardButton(
                    text=f"دفع {agent[i + 1].method}",
                    callback_data=f"request {agent[i + 1].method}",
                )
            )
        keyboard.append(row)
    return keyboard


async def get_order_message(group_id: int, message_id: int, worker_id: int):
    cpyro = PyroClientSingleton()
    old_message = await cpyro.get_messages(chat_id=group_id, message_ids=message_id)
    message = await cpyro.copy_message(
        chat_id=worker_id,
        from_chat_id=group_id,
        message_id=message_id,
        reply_markup=old_message.reply_markup,
    )
    return message


async def send_requested_order(
    serial: int,
    message_id: int,
    group_id: int,
    worker_id: int,
    order_type: str,
    operation: str,
):
    message = await get_order_message(group_id, message_id, worker_id)
    if order_type.startswith("check"):
        await parent_to_child_models_mapper[operation].add_message_ids(
            serial=serial,
            checking_message_id=message.id,
        )
    else:
        await parent_to_child_models_mapper[operation].add_message_ids(
            serial=serial,
            processing_message_id=message.id,
        )
    await parent_to_child_models_mapper[operation].set_working_on_it(
        serial=serial,
        working_on_it=1,
        worker_id=worker_id,
    )
