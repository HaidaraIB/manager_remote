from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from common.common import notify_workers
from models import WithdrawOrder, Account, Checker, PaymentAgent
from common.constants import *
import asyncio


SEND_WITHDRAW_CODE_TEXT = (
    "أرسل كود السحب\n\n"
    "يوضح الفيديو المرفق كيفية الحصول على الكود.\n\n"
    "Send the withdraw code\n\n"
    "The video shows how you can get it."
)

DUPLICATE_CODE_TEXT = (
    "لقد تم إرسال هذا الكود إلى البوت من قبل ❗️\n\n"
    "Duplicate code ❗️"
)

def stringify_order(
    w_type: str,
    acc_number: int,
    password: str,
    withdraw_code: str,
    method: str,
    serial: int,
    method_info: str,
):
    g_b_dict = {"gift": "مكافأة", "balance": "رصيد"}
    return (
        f"تفاصيل طلب سحب {g_b_dict[w_type]}:\n\n"
        f"رقم الحساب 🔢: <code>{acc_number}</code>\n"
        f"كلمة المرور 🈴: <code>{password}</code>\n"
        f"كود السحب: <code>{withdraw_code}</code>\n"
        f"وسيلة الدفع 💳: <b>{method}</b>\n\n"
        f"Serial: <code>{serial}</code>\n\n"
        f"{method_info}\n\n"
        f"تحقق من توفر المبلغ وقم بقبول/رفض الطلب بناء على ذلك.\n"
    )


async def send_withdraw_order_to_check(
    context: ContextTypes.DEFAULT_TYPE,
    withdraw_code: str,
    method: str,
    target_group: int,
    user_id: int,
    acc_number: str,
    bank_account_name: str,
    payment_method_number: str,
    w_type: str,
    password: str = None,
    agent_id: int = None,
):

    code_present = WithdrawOrder.check_withdraw_code(withdraw_code=withdraw_code)

    if code_present and code_present.state == "approved":
        return False

    serial = await WithdrawOrder.add_withdraw_order(
        group_id=target_group,
        user_id=user_id,
        method=method,
        acc_number=acc_number,
        withdraw_code=withdraw_code,
        bank_account_name=bank_account_name,
        payment_method_number=payment_method_number,
        agent_id=agent_id,
    )

    method_info = f"<b>Payment info</b>: <code>{payment_method_number}</code>" + (
        f"\nاسم صاحب الحساب: <b>{bank_account_name}</b>"
        if method in [BARAKAH, BARAKAH]
        else ""
    )
    message = await context.bot.send_message(
        chat_id=target_group,
        text=stringify_order(
            w_type=w_type,
            acc_number=acc_number,
            password=password,
            withdraw_code=withdraw_code,
            method=method,
            serial=serial,
            method_info=method_info,
        ),
        reply_markup=InlineKeyboardMarkup.from_button(
            InlineKeyboardButton(
                text="التحقق ☑️", callback_data=f"check_withdraw_order_{serial}"
            )
        ),
    )

    await WithdrawOrder.add_message_ids(
        serial=serial,
        pending_check_message_id=message.id,
    )

    workers = Checker.get_workers(check_what="withdraw")
    asyncio.create_task(
        notify_workers(
            context=context,
            workers=workers,
            text=f"انتباه يوجد طلب تحقق سحب {method} جديد 🚨",
        )
    )

    workers = PaymentAgent.get_workers(method=method)
    asyncio.create_task(
        notify_workers(
            context=context,
            workers=workers,
            text=f"انتباه يوجد طلب سحب {method} قيد التحقق 🚨",
        )
    )
    return True
