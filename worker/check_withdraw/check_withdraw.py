from telegram import (
    Chat,
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from custom_filters import Withdraw, Declined

from DB import DB
import os

from common.common import (
    build_worker_keyboard,
)

DECLINE_REASON = 0


def stringify_order(
    amount: float,
    serial: int,
    method: str,
    payment_method_number: str,
):
    return (
        "تفاصيل طلب سحب :\n\n"
        f"المبلغ💵: <code>{amount}</code>\n\n"
        f"Serial: <code>{serial}</code>\n\n"
        f"وسيلة الدفع: <code>{method}</code>\n\n"
        f"Payment Info: <code>{payment_method_number}</code>\n\n"
        "تنبيه: اضغط على رقم المحفظة والمبلغ لنسخها كما هي في الرسالة تفادياً للخطأ."
    )


async def check_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        # if update.effective_user.id in context.bot_data['suspended_workers']:
        #     await update.callback_query.answer("تم إيقافك عن العمل إلى حين معالجة الشكاوى الصادرة باسمك.")
        #     return

        serial = int(update.callback_query.data.split("_")[-1])

        await DB.add_checker_id(
            order_type="withdraw",
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


async def send_withdraw_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        serial = int(update.callback_query.data.split("_")[-1])
        w_order = DB.get_one_order(order_type="withdraw", serial=serial)

        method = w_order["method"]
        target_group = f"{method}_group"

        message = await context.bot.send_message(
            chat_id=context.bot_data["data"][target_group],
            text=stringify_order(
                w_order["amount"],
                serial=serial,
                method=method,
                payment_method_number=w_order["payment_method_number"],
            ),
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="قبول الطلب✅",
                    callback_data=f"verify_withdraw_order_{serial}",
                )
            ),
        )

        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="تم إرسال الطلب✅",
                    callback_data="✅✅✅✅✅✅✅✅✅",
                )
            )
        )

        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text="تم إرسال الطلب✅",
            reply_markup=build_worker_keyboard(),
        )

        context.user_data["requested"] = False
        await DB.send_order(
            order_type="withdraw",
            pending_process_message_id=message.id,
            serial=serial,
            group_id=context.bot_data["data"][target_group],
        )


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

        w_order = DB.get_one_order(order_type="withdraw", serial=serial)

        text_list = update.message.reply_to_message.text.split("\n")
        amount = w_order["amount"]
        user_id = w_order["user_id"]

        if text_list[0].startswith("تفاصيل طلب سحب مكافأة"):
            await DB.update_gifts_balance(user_id=user_id, amount=amount)

        text = (
            f"تم رفض عملية سحب مبلغ <b>{amount}$</b>❗️\n\n"
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

        text = update.message.reply_to_message.text_html.split("\n")
        text.insert(0, "تم رفض الطلب❌")
        text = "\n".join(text) + f"\n\nالسبب:\n<b>{update.message.text_html}</b>"
        message = await context.bot.send_message(
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
            reply_markup=build_worker_keyboard(),
        )

        context.user_data["requested"] = False
        await DB.decline_order(
            order_type="withdraw",
            archive_message_ids=str(message.id),
            reason=update.message.text,
            serial=serial,
        )
        return ConversationHandler.END


async def back_from_decline_withdraw_order(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
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
        return ConversationHandler.END


check_payment_handler = CallbackQueryHandler(
    callback=check_payment,
    pattern="^check_withdraw_order",
)

send_withdraw_order_handler = CallbackQueryHandler(
    callback=send_withdraw_order,
    pattern="^send_withdraw_order",
)

decline_withdraw_order_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            callback=decline_withdraw_order,
            pattern="^decline_withdraw_order",
        )
    ],
    states={
        DECLINE_REASON: [
            MessageHandler(
                filters=filters.REPLY & filters.TEXT & Withdraw() & Declined(),
                callback=decline_withdraw_order_reason,
            )
        ]
    },
    fallbacks=[
        CallbackQueryHandler(
            callback=back_from_decline_withdraw_order,
            pattern="^back_from_decline_withdraw_order",
        )
    ],
    name="decline_withdraw_order_handler",
    persistent=True,
)
