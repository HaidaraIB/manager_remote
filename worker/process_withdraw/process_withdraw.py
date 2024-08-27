from telegram import Chat, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
import os
import datetime
from custom_filters import Withdraw, Returned, DepositAgent, Approved
from models import WithdrawOrder, ReturnedConv
from common.common import (
    build_worker_keyboard,
    pretty_time_delta,
    format_amount,
    send_to_photos_archive,
    send_photo_to_user,
)
from worker.process_withdraw.common import (
    return_order_to_user,
    return_order_to_checker,
    build_process_withdraw_keyboard,
)


async def user_payment_verified(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        serial = int(update.callback_query.data.split("_")[-1])

        order = WithdrawOrder.get_one_order(serial=serial)
        if order.state == "deleted":
            keyboard = [
                [
                    InlineKeyboardButton(
                        text="طلب محذوف ⁉️",
                        callback_data="!?!?!?!?!?!?!?!?!?!?!?",
                    )
                ]
            ]
            text = "لقد قامت الإدارة بحذف هذا الطلب ⁉️"
        else:
            keyboard = build_process_withdraw_keyboard(serial)
            text = (
                "قم بالرد على هذه الرسالة بصورة لإشعار الدفع، في حال وجود مشكلة في المبلغ قم بالإعادة إلى الموظف المسؤول، "
                "أو يمكنك الإعادة إلى المستخدم في حال وجود مشكلة في معلومات الدفع الخاصة به."
            )

        await update.callback_query.answer(text=text, show_alert=True)
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(keyboard)
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
            f"الرقم التسلسلي للطلب: <code>{serial}</code>"
        )

        await send_photo_to_user(
            update=update,
            context=context,
            user_id=user_id,
            photo=update.message.photo[-1],
            msg=caption,
        )

        caption = "تمت الموافقة ✅\n" + update.message.reply_to_message.text_html

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
                    text="تمت الموافقة ✅",
                    callback_data="✅✅✅✅✅✅✅✅✅",
                ),
            ),
        )

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="تمت الموافقة ✅",
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

        await WithdrawOrder.approve_payment_order(
            amount=amount,
            method=w_order.method,
            serial=serial,
            worker_id=update.effective_user.id,
        )
        await send_to_photos_archive(
            context=context,
            photo=update.message.photo[-1],
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
                    text=(
                        "الرجوع عن الإعادة إلى المستخدم 🔙"
                        if "return_to_checker" not in update.callback_query.data
                        else "الرجوع عن الإعادة إلى الموظف 🔙"
                    ),
                    callback_data=(
                        f"back_from_return_withdraw_order_{serial}"
                        if "return_to_checker" not in update.callback_query.data
                        else f"back_from_return_to_checker_withdraw_order_{serial}"
                    ),
                )
            )
        )


async def return_withdraw_order_reason(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:
        data = update.message.reply_to_message.reply_markup.inline_keyboard[0][
            0
        ].callback_data
        serial = int(data.split("_")[-1])
        w_order = WithdrawOrder.get_one_order(serial=serial)
        reason = update.message.text_html
        
        await ReturnedConv.add_response(
            serial=serial,
            order_type="withdraw",
            worker_id=update.effective_user.id,
            msg=reason,
            from_user=False,
        )

        if "return_to_checker" in data:
            await return_order_to_checker(
                context=context,
                w_order=w_order,
                reason=reason,
            )
            return_to_who_line = "تمت إعادة الطلب إلى الموظف 📥"
        else:
            message = await return_order_to_user(
                update=update,
                context=context,
                w_order=w_order,
            )
            if not message:
                return_to_who_line = "لقد قام هذا المستخدم بحظر البوت"
            else:
                return_to_who_line = "تمت إعادة الطلب إلى المستخدم 📥"
                await WithdrawOrder.add_message_ids(
                    serial=serial,
                    returned_message_id=message.id,
                )

        text = (
            return_to_who_line
            + "\n"
            + update.message.reply_to_message.text_html
            + f"\n\nسبب الإعادة:\n<b>{reason}</b>"
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
                    text=return_to_who_line,
                    callback_data="📥📥📥📥📥📥📥📥",
                ),
            ),
        )

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=return_to_who_line,
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
                text=(
                    f"طلب متأخر بمقدار\n"
                    + f"<code>{pretty_time_delta(latency.total_seconds() - 600)}</code>\n"
                    f"الموظف المسؤول {update.effective_user.name}\n\n" + text
                ),
            )


async def back_from_return_withdraw_order(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        serial = int(update.callback_query.data.split("_")[-1])

        await update.callback_query.answer(
            text=(
                "قم بالرد على هذه الرسالة بصورة لإشعار الدفع، في حال وجود مشكلة في المبلغ قم بالإعادة إلى الموظف المسؤول، "
                "أو يمكنك الإعادة إلى المستخدم في حال وجود مشكلة في معلومات الدفع الخاصة به."
            ),
            show_alert=True,
        )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(build_process_withdraw_keyboard(serial))
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
    pattern="^return(_to_checker)?_withdraw_order",
)
return_withdraw_order_reason_handler = MessageHandler(
    filters=filters.REPLY & filters.TEXT & Withdraw() & Returned(),
    callback=return_withdraw_order_reason,
)
back_from_return_withdraw_order_handler = CallbackQueryHandler(
    callback=back_from_return_withdraw_order,
    pattern="^back_from_return(_to_checker)?_withdraw_order",
)
