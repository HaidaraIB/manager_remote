from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from common.common import notify_workers, build_back_button
from common.back_to_home_page import back_to_user_home_page_button
from models import WithdrawOrder, Checker, PaymentAgent
from common.constants import *
from common.stringifies import stringify_check_withdraw_order
import asyncio


SEND_WITHDRAW_CODE_TEXT = (
    "أرسل كود السحب\n\n"
    "يوضح الفيديو المرفق كيفية الحصول على الكود.\n\n"
    "Send the withdraw code\n\n"
    "The video shows how you can get it."
)

DUPLICATE_CODE_TEXT = (
    "لقد تم إرسال هذا الكود إلى البوت من قبل ❗️\n\n" "Duplicate code ❗️"
)


async def send_withdraw_order_to_check(
    context: ContextTypes.DEFAULT_TYPE,
    update: Update,
    password: str,
):
    withdraw_code = update.message.text
    code_present = WithdrawOrder.check_withdraw_code(withdraw_code=withdraw_code)
    if code_present and code_present.state == "approved":
        return False
    
    acc_number = context.user_data["withdraw_account"]
    aeban_number = context.user_data.get("aeban_number", "")
    bank_account_name = context.user_data.get("bank_account_name", "")
    method = context.user_data["payment_method"]
    payment_method_number = context.user_data["payment_method_number"]
    target_group = context.bot_data["data"]["withdraw_orders_group"]
    w_type = context.user_data.get("withdraw_type", "balance")
    user_id = update.effective_user.id

    serial = await WithdrawOrder.add_withdraw_order(
        group_id=target_group,
        user_id=user_id,
        method=method,
        acc_number=acc_number,
        withdraw_code=withdraw_code,
        aeban_number=aeban_number,
        bank_account_name=bank_account_name,
        payment_method_number=payment_method_number,
    )

    method_info = f"<b>Payment info</b>: <code>{payment_method_number}</code>"
    if method in AEBAN_LIST:
        method_info += (
            f"\nرقم الآيبان: <b>{aeban_number}</b>"
            + f"\nاسم صاحب الحساب: <b>{bank_account_name}</b>"
        )
    elif method not in CRYPTO_LIST:
        method_info += +f"\nاسم صاحب الحساب: <b>{bank_account_name}</b>"

    message = await context.bot.send_message(
        chat_id=target_group,
        text=stringify_check_withdraw_order(
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


async def request_bank_account_name(update: Update, back_keyboard):
    if update.message:
        await update.message.reply_text(
            text=SEND_BANK_ACCOUNT_NAME_TEXT,
            reply_markup=InlineKeyboardMarkup(back_keyboard),
        )
    else:
        await update.callback_query.edit_message_text(
            text=SEND_BANK_ACCOUNT_NAME_TEXT,
            reply_markup=InlineKeyboardMarkup(back_keyboard),
        )


async def request_aeban_number(update: Update, back_keyboard):
    if update.message:
        await update.message.reply_text(
            text=SEND_AEBAN_NUMBER_TEXT,
            reply_markup=InlineKeyboardMarkup(back_keyboard),
        )
    else:
        await update.callback_query.edit_message_text(
            text=SEND_AEBAN_NUMBER_TEXT,
            reply_markup=InlineKeyboardMarkup(back_keyboard),
        )
