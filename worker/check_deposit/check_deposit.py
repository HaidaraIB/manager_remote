from telegram import (
    Update,
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from common.common import (
    apply_ex_rate,
    notify_workers,
    build_worker_keyboard,
)
import models
import os
import asyncio

from custom_filters import Declined, DepositAgent, Deposit


async def check_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        # if update.effective_user.id in context.bot_data['suspended_workers']:
        #     await update.callback_query.answer("تم إيقافك عن العمل إلى حين معالجة الشكاوى الصادرة باسمك.")
        #     return

        serial = int(update.callback_query.data.split("_")[-1])

        await models.DepositOrder.add_checker_id(
            serial=serial,
            checker_id=update.effective_user.id,
        )

        payment_ok_buttons = [
            [
                InlineKeyboardButton(
                    text="إرسال الطلب⬅️", callback_data=f"send_deposit_order_{serial}"
                ),
                InlineKeyboardButton(
                    text="رفض الطلب❌", callback_data=f"decline_deposit_order_{serial}"
                ),
            ]
        ]
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(payment_ok_buttons),
        )


async def send_deposit_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:
        serial = int(update.callback_query.data.split("_")[-1])
        d_order = models.DepositOrder.get_one_order(serial=serial)

        amount, ex_rate = apply_ex_rate(
            method=d_order.method,
            amount=d_order.amount,
            order_type="deposit",
            context=context,
        )
        order_text = stringify_order(
            amount=amount,
            account_number=d_order.acc_number,
            method=d_order.method,
            serial=d_order.serial,
        )
        message = await context.bot.send_photo(
            chat_id=context.bot_data["data"]["deposit_after_check_group"],
            photo=update.effective_message.photo[-1],
            caption=order_text,
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="قبول الطلب ✅", callback_data=f"verify_deposit_order_{serial}"
                )
            ),
        )

        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="تم إرسال الطلب ✅",
                    callback_data="✅✅✅✅✅✅✅✅✅✅",
                )
            )
        )

        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text="تم إرسال الطلب ✅",
            reply_markup=build_worker_keyboard(
                deposit_agent=DepositAgent().filter(update)
            ),
        )

        await models.DepositOrder.send_order(
            pending_process_message_id=message.id,
            serial=serial,
            group_id=context.bot_data["data"]["deposit_after_check_group"],
            ex_rate=ex_rate,
        )
        workers = models.DepositAgent.get_workers()
        asyncio.create_task(
            notify_workers(
                context=context,
                workers=workers,
                text=f"انتباه تم استلام إيداع جديد 🚨",
            )
        )
        context.user_data["requested"] = False


async def decline_deposit_order(update: Update, _: ContextTypes.DEFAULT_TYPE):
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
                    text="الرجوع عن الرفض 🔙",
                    callback_data=f"back_from_decline_deposit_order_{serial}",
                )
            )
        )


async def decline_deposit_order_reason(
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

        d_order = models.DepositOrder.get_one_order(serial=serial)

        text = (
            "تم رفض الطلب❌\n"
            + stringify_order(
                amount=d_order.amount,
                account_number=d_order.acc_number,
                method=d_order.method,
                serial=d_order.serial,
            )
            + f"\n\nالسبب:\n<b>{update.message.text_html}</b>"
        )
        try:
            await context.bot.send_message(chat_id=d_order.user_id, text=text)
        except:
            pass

        caption = (
            "تم رفض الطلب❌\n"
            + update.message.reply_to_message.caption_html
            + f"\n\nالسبب:\n<b>{update.message.text_html}</b>"
        )

        await context.bot.send_photo(
            chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
            photo=update.message.reply_to_message.photo[-1],
            caption=caption,
        )

        await context.bot.edit_message_reply_markup(
            chat_id=update.effective_chat.id,
            message_id=update.message.reply_to_message.id,
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="تم رفض الطلب ❌",
                    callback_data="❌❌❌❌❌❌❌",
                )
            ),
        )

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="تم رفض الطلب ❌",
            reply_markup=build_worker_keyboard(
                deposit_agent=DepositAgent().filter(update)
            ),
        )
        await models.DepositOrder.decline_order(
            reason=update.message.text,
            serial=serial,
        )

        context.user_data["requested"] = False


async def back_from_decline_deposit_order(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP]:

        serial = int(update.callback_query.data.split("_")[-1])

        payment_ok_buttons = [
            [
                InlineKeyboardButton(
                    text="إرسال الطلب ⬅️", callback_data=f"send_deposit_order_{serial}"
                ),
                InlineKeyboardButton(
                    text="رفض الطلب ❌", callback_data=f"decline_deposit_order_{serial}"
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
    account_number: int,
    *args,
):
    return (
        "إيداع جديد:\n"
        f"المبلغ 💵: <code>{amount if amount else 'لا يوجد بعد'}</code>\n"
        f"رقم الحساب: <code>{account_number}</code>\n\n"
        f"وسيلة الدفع: <code>{method}</code>\n\n"
        f"Serial: <code>{serial}</code>\n\n"
        "تنبيه: اضغط على رقم الحساب والمبلغ لنسخها كما هي في الرسالة تفادياً للخطأ."
    )


check_deposit_handler = CallbackQueryHandler(
    callback=check_deposit,
    pattern="^check_deposit",
)

send_deposit_order_handler = CallbackQueryHandler(
    callback=send_deposit_order,
    pattern="^send_deposit_order",
)

decline_deposit_order_handler = CallbackQueryHandler(
    callback=decline_deposit_order,
    pattern="^decline_deposit_order",
)
decline_deposit_order_reason_handler = MessageHandler(
    filters=filters.REPLY & filters.TEXT & Deposit() & Declined(),
    callback=decline_deposit_order_reason,
)
back_from_decline_deposit_order_handler = CallbackQueryHandler(
    callback=back_from_decline_deposit_order,
    pattern="^back_from_decline_deposit_order",
)
