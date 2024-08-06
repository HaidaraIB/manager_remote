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
    send_media,
)
from worker.check_deposit.common import build_check_deposit_keyboard
import models
import os
import asyncio

from custom_filters import Declined, DepositAgent, Deposit, DepositAmount


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

        await update.callback_query.edit_message_reply_markup(
            reply_markup=build_check_deposit_keyboard(serial),
        )


async def edit_deposit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:
        serial = int(update.callback_query.data.split("_")[-1])

        await update.callback_query.answer(
            text="قم بالرد على هذه الرسالة بالمبلغ الجديد",
            show_alert=True,
        )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="الرجوع عن تعديل المبلغ 🔙",
                    callback_data=f"back_from_edit_deposit_amount_{serial}",
                )
            )
        )


async def get_new_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:
        serial = int(
            update.message.reply_to_message.reply_markup.inline_keyboard[0][
                0
            ].callback_data.split("_")[-1]
        )
        d_order = models.DepositOrder.get_one_order(serial=serial)
        new_amount = float(update.message.text)
        await models.DepositOrder.edit_order_amount(
            new_amount=new_amount, serial=serial
        )

        await update.message.delete()

        await update.message.reply_to_message.edit_caption(
            caption=stringify_order(
                amount=new_amount,
                serial=serial,
                account_number=d_order.acc_number,
                method=d_order.method,
                wal=d_order.deposit_wallet,
            )
            + "\n\nتم تعديل المبلغ ✅",
            reply_markup=build_check_deposit_keyboard(serial),
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
        message = await send_media(
            context=context,
            chat_id=context.bot_data["data"]["deposit_after_check_group"],
            media=update.effective_message.photo[-1] if update.effective_message.photo else update.effective_message.document,
            caption=stringify_order(
                amount=amount,
                account_number=d_order.acc_number,
                method=d_order.method,
                serial=d_order.serial,
                wal=d_order.deposit_wallet,
            ),
            markup=InlineKeyboardMarkup.from_button(
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
                wal=d_order.deposit_wallet,
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

        await send_media(
            context=context,
            media=(
                update.message.reply_to_message.photo[-1]
                if update.message.reply_to_message.photo
                else update.message.reply_to_message.document
            ),
            chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
            caption=caption
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


async def back_to_check_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        serial = int(update.callback_query.data.split("_")[-1])

        await update.callback_query.edit_message_reply_markup(
            reply_markup=build_check_deposit_keyboard(serial)
        )


def stringify_order(
    amount: float,
    serial: int,
    method: str,
    account_number: int,
    wal:str,
    *args,
):
    return (
        "إيداع جديد:\n"
        f"المبلغ 💵: <code>{amount if amount else 'لا يوجد بعد'}</code>\n"
        f"رقم الحساب: <code>{account_number}</code>\n\n"
        f"وسيلة الدفع: <code>{method}</code>\n"
        f"المحفظة: <code>{wal}</code>\n\n"
        f"Serial: <code>{serial}</code>\n\n"
        "تنبيه: اضغط على رقم الحساب والمبلغ لنسخها كما هي في الرسالة تفادياً للخطأ."
    )


check_deposit_handler = CallbackQueryHandler(
    callback=check_deposit,
    pattern="^check_deposit",
)

edit_deposit_amount_handler = CallbackQueryHandler(
    callback=edit_deposit_amount,
    pattern="^edit_deposit_amount",
)
get_new_amount_handler = MessageHandler(
    filters=filters.REPLY & filters.Regex("^\d+.?\d*$") & Deposit() & DepositAmount(),
    callback=get_new_amount,
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
    callback=back_to_check_deposit,
    pattern="^back_from_((decline_deposit_order)|(edit_deposit_amount))",
)
