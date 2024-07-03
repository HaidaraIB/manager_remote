from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    ContextTypes,
)

from DB import DB
import os
from common.common import apply_ex_rate


async def check_deposit(context: ContextTypes.DEFAULT_TYPE):
    check_deposit_jobs_dict = {
        "1_deposit_check": 240,
        "2_deposit_check": 240,
        "3_deposit_check": 840,
        "4_deposit_check": 5040,
    }
    serial = int(context.job.data)
    d_order = DB.get_one_order(
        "deposit",
        serial=serial,
    )
    ref_present = DB.get_ref_number(
        number=d_order["ref_number"],
        method=d_order["method"],
    )
    if ref_present:
        await send_order_to_process(
            d_order=d_order,
            ref_info=ref_present,
            context=context,
        )
    elif context.job.name in check_deposit_jobs_dict:
        next_job_num = int(context.job.name.split("_")[0]) + 1
        context.job_queue.run_once(
            callback=check_deposit,
            user_id=context.job.user_id,
            when=check_deposit_jobs_dict[context.job.name],
            data=serial,
            name=f"{next_job_num}_deposit_check",
            job_kwargs={
                "misfire_grace_time": None,
                "coalesce": True,
            },
        )
    else:
        reason = "لم يجد البوت رقم عملية الدفع المرتبط بهذا الطلب"
        await context.bot.send_message(
            chat_id=context.job.user_id,
            text=(
                f"{reason}\n\n"
                f"الرقم التسلسلي للطلب: {serial}\n"
                f"نوع الطلب: إيداع\n\n"
                "عليك التحقق وإعادة الطلب مرة أخرى، سيتم التحقق بشكل دوري."
            ),
        )
        text = stringify_order(
            amount="لا يوجد",
            account_number=d_order["acc_number"],
            method=d_order["method"],
            serial=d_order["serial"],
            ref_num=d_order["ref_number"],
        )
        text_list = text.split("\n")
        text_list.insert(0, "تم رفض الطلب❌")
        text = "\n".join(text_list) + f"\n\nالسبب:\n<b>{reason}</b>"

        message = await context.bot.send_message(
            chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
            text=text,
        )
        await DB.set_deposit_not_arrived(
            reason=reason, serial=serial, archive_message_ids=message.id
        )


async def send_order_to_process(d_order, ref_info, context: ContextTypes.DEFAULT_TYPE):
    amount, ex_rate = apply_ex_rate(
        d_order["method"],
        ref_info["amount"],
        "deposit",
        context,
    )

    message = await context.bot.send_message(
        chat_id=context.bot_data["data"]["deposit_after_check_group"],
        text=stringify_order(
            amount=amount,
            account_number=d_order["acc_number"],
            method=d_order["method"],
            serial=d_order["serial"],
            ref_num=ref_info["number"],
        ),
        reply_markup=InlineKeyboardMarkup.from_button(
            InlineKeyboardButton(
                text="قبول الطلب✅",
                callback_data=f"verify_deposit_order_{d_order['serial']}",
            )
        ),
    )
    await DB.send_order(
        order_type="deposit",
        pending_process_message_id=message.id,
        serial=d_order["serial"],
        ref_info=ref_info,
        group_id=context.bot_data["data"]["deposit_after_check_group"],
        ex_rate=ex_rate,
    )


def stringify_order(
    amount: float, serial: int, method: str, account_number: int, ref_num: str, *args
):
    return (
        "إيداع جديد:\n"
        f"رقم العملية: {ref_num}\n"
        f"المبلغ: <code>{amount}</code>\n"
        f"رقم الحساب: <code>{account_number}</code>\n\n"
        f"وسيلة الدفع: <code>{method}</code>\n\n"
        f"Serial: <code>{serial}</code>\n\n"
        "تنبيه: اضغط على رقم الحساب والمبلغ لنسخها كما هي في الرسالة تفادياً للخطأ.\n\n"
        "ملاحظة: تأكد من تطابق المبلغ في الرسالة مع الذي في لقطة الشاشة لأن ما سيضاف في حالة التأكيد هو الذي في الرسالة."
    )
