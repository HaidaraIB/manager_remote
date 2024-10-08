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



def build_checker_keyboard(checker: list[models.Checker]):
    usdt = []
    syr = []
    banks = []
    payeer = []
    point_deposit = []
    for c in checker:
        button = InlineKeyboardButton(
            text=f"تحقق {c.method}",
            callback_data=f"request_check_{c.check_what}_{c.method}",
        )
        if c.method == USDT:
            usdt.append(button)
        elif c.method in [BARAKAH, BEMO]:
            banks.append(button)
        elif c.method in [SYRCASH, MTNCASH]:
            syr.append(button)
        elif c.method == POINT_DEPOSIT:
            point_deposit.append(button)
        else:
            payeer.append(button)
    return [usdt, syr, banks, payeer, point_deposit]


def build_payment_agent_keyboard(agent: list[models.PaymentAgent]):
    usdt = []
    syr = []
    banks = []
    payeer = []
    for m in agent:
        button = InlineKeyboardButton(
            text=f"دفع {m.method}",
            callback_data=f"request_{m.method}",
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
    order_type: str,
    message_id: int,
    group_id: int,
    worker_id: int,
    checker_id:int,
    state: str,
):
    message = await get_order_message(group_id, message_id, worker_id)
    await parent_to_child_models_mapper[order_type].add_message_ids(
        serial=serial,
        checking_message_id=message.id if state == "checking" else 0,
        processing_message_id=message.id if state == "processing" else 0,
    )
    await parent_to_child_models_mapper[order_type].set_working_on_it(
        serial=serial,
        checker_id=checker_id,
        worker_id=worker_id,
        state=state,
    )
