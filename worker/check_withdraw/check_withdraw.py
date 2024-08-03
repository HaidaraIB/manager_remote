from telegram import (
    Chat,
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from custom_filters import Withdraw, Declined, Sent, DepositAgent
from models import WithdrawOrder, PaymentAgent
from constants import *
import os
import asyncio

from common.common import (
    build_worker_keyboard,
    apply_ex_rate,
    notify_workers,
    format_amount,
)

(
    DECLINE_REASON,
    AMOUNT,
) = range(2)


async def check_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        # if update.effective_user.id in context.bot_data['suspended_workers']:
        #     await update.callback_query.answer("تم إيقافك عن العمل إلى حين معالجة الشكاوى الصادرة باسمك.")
        #     return

        serial = int(update.callback_query.data.split("_")[-1])

        await WithdrawOrder.add_checker_id(
            serial=serial,
            checker_id=update.effective_user.id,
        )

        payment_ok_buttons = [
            [
                InlineKeyboardButton(
                    text="إرسال الطلب⬅️",
                    callback_data=f"send_withdraw_order_{serial}",
                ),
                InlineKeyboardButton(
                    text="رفض طلب السحب❌",
                    callback_data=f"decline_withdraw_order_{serial}",
                ),
            ]
        ]
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(payment_ok_buttons),
        )


async def get_withdraw_order_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:
        serial = int(update.callback_query.data.split("_")[-1])

        await update.callback_query.answer(
            text="قم بالرد على هذه الرسالة بمبلغ السحب",
            show_alert=True,
        )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="الرجوع عن المبلغ 🔙",
                    callback_data=f"back_from_get_withdraw_order_amount_{serial}",
                )
            )
        )
        return AMOUNT


async def send_withdraw_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:
        serial = int(
            update.message.reply_to_message.reply_markup.inline_keyboard[0][
                0
            ].callback_data.split("_")[-1]
        )
        amount = float(update.message.text)
        await WithdrawOrder.edit_order_amount(
            new_amount=amount,
            serial=serial,
        )

        w_order = WithdrawOrder.get_one_order(serial=serial)

        method = w_order.method
        target_group = f"{method}_group"

        amount, ex_rate = apply_ex_rate(
            method=method,
            amount=amount,
            order_type="withdraw",
            context=context,
        )

        order_text = stringify_order(
            amount=amount,
            serial=serial,
            method=method,
            payment_method_number=w_order.payment_method_number,
        )

        message = await context.bot.send_message(
            chat_id=context.bot_data["data"][target_group],
            text=order_text,
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="قبول الطلب✅",
                    callback_data=f"verify_withdraw_order_{serial}",
                )
            ),
        )

        await context.bot.edit_message_reply_markup(
            chat_id=update.effective_chat.id,
            message_id=update.message.reply_to_message.id,
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="تم إرسال الطلب✅",
                    callback_data="✅✅✅✅✅✅✅✅✅",
                )
            ),
        )

        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text="تم إرسال الطلب✅",
            reply_markup=build_worker_keyboard(
                deposit_agent=DepositAgent().filter(update),
            ),
        )

        await WithdrawOrder.send_order(
            pending_process_message_id=message.id,
            serial=serial,
            group_id=context.bot_data["data"][target_group],
            ex_rate=ex_rate,
        )
        workers = PaymentAgent.get_workers(method=method)

        asyncio.create_task(
            notify_workers(
                context=context,
                workers=workers,
                text=f"انتباه تم استلام سحب {method} جديد 🚨",
            )
        )
        context.user_data["requested"] = False


async def decline_withdraw_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        serial = int(update.callback_query.data.split("_")[-1])

        await update.callback_query.answer(
            text="قم بالرد على هذه الرسالة بسبب الرفض",
            show_alert=True,
        )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="الرجوع عن الرفض🔙",
                    callback_data=f"back_from_decline_withdraw_order_{serial}",
                )
            )
        )
        return DECLINE_REASON


async def decline_withdraw_order_reason(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        serial = int(
            update.message.reply_to_message.reply_markup.inline_keyboard[0][
                0
            ].callback_data.split("_")[-1]
        )

        w_order = WithdrawOrder.get_one_order(serial=serial)

        w_code = w_order.withdraw_code
        user_id = w_order.user_id

        text = (
            f"تم رفض عملية السحب ذات الكود <b>{w_code}</b>❗️\n\n"
            "السبب:\n"
            f"<b>{update.message.text_html}</b>\n\n"
            f"الرقم التسلسلي للطلب: <code>{serial}</code>\n\n"
        )
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=text,
            )
        except:
            pass

        text = (
            "تم رفض الطلب❌\n"
            + update.message.reply_to_message.text_html
            + f"\n\nالسبب:\n<b>{update.message.text_html}</b>"
        )

        await context.bot.send_message(
            chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
            text=text,
        )

        await context.bot.edit_message_reply_markup(
            chat_id=update.effective_chat.id,
            message_id=update.message.reply_to_message.id,
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="تم رفض الطلب❌",
                    callback_data="❌❌❌❌❌❌❌",
                )
            ),
        )

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="تم رفض الطلب❌",
            reply_markup=build_worker_keyboard(
                deposit_agent=DepositAgent().filter(update),
            ),
        )

        await WithdrawOrder.decline_order(
            reason=update.message.text,
            serial=serial,
        )
        context.user_data["requested"] = False


async def back_to_withdraw_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        serial = int(update.callback_query.data.split("_")[-1])

        payment_ok_buttons = [
            [
                InlineKeyboardButton(
                    text="إرسال الطلب⬅️",
                    callback_data=f"send_withdraw_order_{serial}",
                ),
                InlineKeyboardButton(
                    text="رفض طلب السحب❌",
                    callback_data=f"decline_withdraw_order_{serial}",
                ),
            ]
        ]
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(payment_ok_buttons)
        )


def stringify_order(
    amount: float,
    serial: int,
    method: str,
    payment_method_number: str,
    *args,
):
    return (
        "تفاصيل طلب سحب :\n\n"
        f"المبلغ 💵: <code>{amount if amount else 'لا يوجد بعد'}</code>\n\n"
        f"Serial: <code>{serial}</code>\n\n"
        f"وسيلة الدفع: <code>{method}</code>\n\n"
        f"Payment Info: <code>{payment_method_number}</code>\n\n"
        "تنبيه: اضغط على رقم المحفظة والمبلغ لنسخها كما هي في الرسالة تفادياً للخطأ."
    )


check_payment_handler = CallbackQueryHandler(
    callback=check_payment,
    pattern="^check_withdraw_order",
)

back_to_withdraw_check_handler = CallbackQueryHandler(
    callback=back_to_withdraw_check,
    pattern="(^back_from_decline_withdraw_order)|(^back_from_get_withdraw_order_amount)",
)

get_withdraw_order_amount_handler = CallbackQueryHandler(
    callback=get_withdraw_order_amount,
    pattern="^send_withdraw_order",
)
send_withdraw_order_handler = MessageHandler(
    filters=filters.REPLY & filters.Regex("^\d+.?\d*$") & Withdraw() & Sent(),
    callback=send_withdraw_order,
)
decline_withdraw_order_handler = CallbackQueryHandler(
    callback=decline_withdraw_order,
    pattern="^decline_withdraw_order",
)
decline_withdraw_order_reason_handler = MessageHandler(
    filters=filters.REPLY & filters.TEXT & Withdraw() & Declined(),
    callback=decline_withdraw_order_reason,
)
