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
    usdt = []
    syr = []
    banks = []
    payeer = []
    for m in agent:
        button = InlineKeyboardButton(
            text=f"دفع {m.method}",
            callback_data=f"request {m.method}",
        )
        if m.method == USDT:
            usdt.append(button)
        elif m.method in [BARAKAH, BEMO]:
            banks.append(button)
        elif m.method in [SYRCASH, MTNCASH]:
            syr.append(button)
        else:
            payeer.append(button)
    return [usdt, syr, banks, payeer]


async def send_requested_order(
    serial: int,
    message_id: int,
    group_id: int,
    worker_id: int,
    order_type: str,
    operation: str,
):
    cpyro = PyroClientSingleton()
    old_message = await cpyro.get_messages(chat_id=group_id, message_ids=message_id)
    message = await cpyro.copy_message(
        chat_id=worker_id,
        from_chat_id=group_id,
        message_id=message_id,
        reply_markup=old_message.reply_markup,
    )
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
