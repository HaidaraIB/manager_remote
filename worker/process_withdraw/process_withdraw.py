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

import os
import datetime
from custom_filters import Withdraw, Returned, DepositAgent, Approved
from models import WithdrawOrder
from common.common import (
    build_worker_keyboard,
    pretty_time_delta,
    format_amount,
    send_to_media_archive,
)


async def user_payment_verified(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        serial = int(update.callback_query.data.split("_")[-1])

        await update.callback_query.answer(
            text="قم بالرد على هذه الرسالة بصورة لإشعار الدفع، في حال وجود مشكلة يمكنك إعادة الطلب مرفقاً برسالة.",
            show_alert=True,
        )

        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="إعادة الطلب📥",
                    callback_data=f"return_withdraw_order_{serial}",
                )
            )
        )


async def reply_with_payment_proof_withdraw(
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

        amount = w_order.amount
        user_id = w_order.user_id

        caption = (
            f"مبروك، تم تأكيد عملية سحب "
            f"<b>{format_amount(amount)}</b> "
            "بنجاح ✅\n\n"
            f"الرقم التسلسلي للطلب: <code>{serial}</code>\n\n"
            f"Congrats, your withdraw "
            f"<b>{format_amount(amount)}</b> "
            "has been approved ✅\n\n"
            f"Serial: <code>{serial}</code>\n\n"
        )

        try:
            await context.bot.send_photo(
                chat_id=user_id,
                photo=update.message.photo[-1],
                caption=caption,
            )
        except:
            pass

        caption = "تمت الموافقة✅\n" + update.message.reply_to_message.text_html

        await context.bot.send_photo(
            chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
            photo=update.message.photo[-1],
            caption=caption,
        )

        await context.bot.edit_message_reply_markup(
            chat_id=update.effective_chat.id,
            message_id=update.message.reply_to_message.id,
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="تمت الموافقة✅",
                    callback_data="✅✅✅✅✅✅✅✅✅",
                ),
            ),
        )

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="تمت الموافقة✅",
            reply_markup=build_worker_keyboard(
                deposit_agent=DepositAgent().filter(update)
            ),
        )

        prev_date = (
            w_order.send_date if w_order.state != "returned" else w_order.return_date
        )
        latency = datetime.datetime.now() - prev_date
        minutes, _ = divmod(latency.total_seconds(), 60)
        if minutes > 10:
            await context.bot.send_photo(
                chat_id=context.bot_data["data"]["latency_group"],
                photo=update.message.photo[-1],
                caption=f"طلب متأخر بمقدار\n"
                + f"<code>{pretty_time_delta(latency.total_seconds() - 600)}</code>\n"
                f"الموظف المسؤول {update.effective_user.name}\n\n" + caption,
            )

        await WithdrawOrder.reply_with_payment_proof(
            amount=amount,
            method=w_order.method,
            serial=serial,
            worker_id=update.effective_user.id,
        )
        await send_to_media_archive(
            context=context,
            media=update.message.photo[-1],
            order_type="withdraw",
            serial=serial,
        )
        


async def return_withdraw_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        serial = int(update.callback_query.data.split("_")[-1])

        await update.callback_query.answer(
            text="قم بالرد على هذه الرسالة بسبب الإعادة",
            show_alert=True,
        )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="الرجوع عن الإعادة🔙",
                    callback_data=f"back_from_return_withdraw_order_{serial}",
                )
            )
        )


async def return_withdraw_order_reason(
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

        withdraw_code = w_order.withdraw_code
        user_id = w_order.user_id

        text = (
            f"تمت إعادة طلب السحب صاحب الكود: <b>{withdraw_code}</b> ❗️\n\n"
            "السبب:\n"
            f"<b>{update.message.text_html}</b>\n\n"
            "قم بالضغط على الزر أدناه وإرفاق المطلوب.\n\n"
            f"The order with the withdraw code has been returned: <b>{withdraw_code}</b> ❗️\n\n"
            "reason:\n"
            f"<b>{update.message.text_html}</b>\n\n"
            "Press the button below to send the neccessary attachments\n\n"
        )

        await context.bot.send_message(
            chat_id=user_id,
            text=text,
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="إرفاق المطلوب - Send Attachments",
                    callback_data=f"handle_return_withdraw_{update.effective_chat.id}_{serial}",
                )
            ),
        )

        text = (
            "تمت إعادة الطلب📥\n"
            + update.message.reply_to_message.text_html
            + f"\n\nسبب الإعادة:\n<b>{update.message.text_html}</b>"
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
                    text="تمت إعادة الطلب📥",
                    callback_data="📥📥📥📥📥📥📥📥",
                ),
            ),
        )

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="تمت إعادة الطلب📥",
            reply_markup=build_worker_keyboard(
                deposit_agent=DepositAgent().filter(update)
            ),
        )

        prev_date = (
            w_order.send_date if w_order.state != "returned" else w_order.return_date
        )
        latency = datetime.datetime.now() - prev_date
        minutes, _ = divmod(latency.total_seconds(), 60)
        if minutes > 10:
            await context.bot.send_message(
                chat_id=context.bot_data["data"]["latency_group"],
                text=f"طلب متأخر بمقدار\n"
                + f"<code>{pretty_time_delta(latency.total_seconds() - 600)}</code>\n"
                f"الموظف المسؤول {update.effective_user.name}\n\n" + text,
            )

        await WithdrawOrder.return_order(
            reason=update.message.text,
            serial=serial,
        )
        


async def back_from_return_withdraw_order(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        serial = int(update.callback_query.data.split("_")[-1])

        await update.callback_query.answer(
            text="قم بالرد على هذه الرسالة بصورة لإشعار الدفع، في حال وجود مشكلة يمكنك إعادة الطلب مرفقاً برسالة.",
            show_alert=True,
        )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="إعادة الطلب📥",
                    callback_data=f"return_withdraw_order_{serial}",
                )
            )
        )


user_payment_verified_handler = CallbackQueryHandler(
    callback=user_payment_verified,
    pattern="^verify_withdraw_order",
)

reply_with_payment_proof_withdraw_handler = MessageHandler(
    filters=filters.REPLY & filters.PHOTO & Withdraw() & Approved(),
    callback=reply_with_payment_proof_withdraw,
)

return_withdraw_order_handler = CallbackQueryHandler(
    callback=return_withdraw_order,
    pattern="^return_withdraw_order",
)
return_withdraw_order_reason_handler = MessageHandler(
    filters=filters.REPLY & filters.TEXT & Withdraw() & Returned(),
    callback=return_withdraw_order_reason,
)
back_from_return_withdraw_order_handler = CallbackQueryHandler(
    callback=back_from_return_withdraw_order,
    pattern="^back_from_return_withdraw_order",
)
