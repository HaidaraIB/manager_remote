from telegram import (
    Chat,
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.constants import (
    ParseMode,
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
import asyncio
import os

from common import (
    build_worker_keyboard,
)

DECLINE_REASON = 0


async def check_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        # if update.effective_user.id in context.bot_data['suspended_workers']:
        #     await update.callback_query.answer("تم إيقافك عن العمل إلى حين معالجة الشكاوى الصادرة باسمك.")
        #     return

        data = update.callback_query.data

        await DB.add_checker_id(
            order_type="withdraw",
            serial=data["serial"],
            checker_id=update.effective_user.id,
        )

        send_withdraw_callback_data = {
            **data,
            "name": "send withdraw order",
            "worker_id": update.effective_user.id,
        }

        decline_withdraw_callback_data = {
            **data,
            "name": "decline withdraw order",
            "worker_id": update.effective_user.id,
        }

        payment_ok_buttons = [
            [
                InlineKeyboardButton(
                    text="إرسال الطلب⬅️", callback_data=send_withdraw_callback_data
                ),
                InlineKeyboardButton(
                    text="رفض طلب السحب❌", callback_data=decline_withdraw_callback_data
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

        data = update.callback_query.data

        verify_button_callback_data = {
            **data,
            "name": "verify withdraw order",
        }

        verify_button = [
            [
                InlineKeyboardButton(
                    text="قبول الطلب✅", callback_data=verify_button_callback_data
                )
            ]
        ]

        text = update.callback_query.message.text_html.split("\n")

        del text[2]
        del text[2]
        del text[2]
        del text[2]
        del text[3]
        del text[7]
        del text[7]

        text.insert(
            7,
            "\n<b>تنبيه: اضغط على رقم المحفظة والمبلغ لنسخها كما هي في الرسالة تفادياً للخطأ.</b>",
        )

        method = data["method"]

        chat_id = f"{method}_group"

        message = await context.bot.send_message(
            chat_id=context.bot_data["data"][chat_id],
            text="\n".join(text),
            reply_markup=InlineKeyboardMarkup(verify_button),
        )

        await DB.change_order_state(
            order_type="withdraw",
            serial=data["serial"],
            state="sent",
        )
        await DB.add_message_ids(
            serial=data["serial"],
            order_type="withdraw",
            pending_process_message_id=message.id,
        )

        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="تم إرسال الطلب✅",
                            callback_data="تم إرسال الطلب✅",
                        )
                    ]
                ]
            )
        )

        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text="تم إرسال الطلب✅",
            reply_markup=build_worker_keyboard(),
        )

        context.user_data["requested"] = False
        await DB.set_working_on_it(
            order_type="withdraw",
            working_on_it=0,
            serial=data["serial"],
        )


async def decline_withdraw_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        data = update.callback_query.data

        decline_button_callback_data = {
            **data,
            "name": "back from decline withdraw order",
        }
        decline_withdraw_button = [
            [
                InlineKeyboardButton(
                    text="الرجوع عن الرفض🔙",
                    callback_data=decline_button_callback_data,
                )
            ],
        ]
        await update.callback_query.answer(
            text="قم بالرد على هذه الرسالة بسبب الرفض",
            show_alert=True,
        )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(decline_withdraw_button)
        )
        return DECLINE_REASON


async def archive_after(
    after: int, context: ContextTypes.DEFAULT_TYPE, text: str, data: dict
):
    await asyncio.sleep(after)
    message = await context.bot.send_message(
        chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
        text=text,
    )

    await DB.add_message_ids(
        archive_message_ids=str(message.id),
        serial=data["serial"],
        order_type="withdraw",
    )


async def decline_withdraw_order_reason(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        data = update.message.reply_to_message.reply_markup.inline_keyboard[0][
            0
        ].callback_data

        text_list = update.message.reply_to_message.text.split("\n")
        await DB.change_order_state(
            order_type="withdraw",
            serial=data["serial"],
            state="declined",
        )
        await DB.add_order_reason(
            order_type="withdraw",
            serial=data["serial"],
            reason=update.message.text,
        )

        amount = data["amount"]
        user_id = data["user_id"]

        if text_list[0].startswith("تفاصيل طلب سحب مكافأة"):
            await DB.update_gifts_balance(user_id=user_id, amount=amount)

        text = f"""تم رفض عملية سحب مبلغ <b>{amount}$</b>❗️

السبب:
<b>{update.message.text_html}</b>

الرقم التسلسلي للطلب: <code>{data['serial']}</code>

"""
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

        await DB.add_message_ids(
            order_type="withdraw",
            archive_message_ids=str(message.id),
            serial=data["serial"],
        )

        await context.bot.edit_message_reply_markup(
            chat_id=update.effective_chat.id,
            message_id=update.message.reply_to_message.id,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(text="تم رفض الطلب❌", callback_data="تم رفض الطلب❌"),
                ]
            ])
        )

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="تم رفض الطلب❌",
            reply_markup=build_worker_keyboard()
        )

        context.user_data["requested"] = False
        await DB.set_working_on_it(
            order_type="withdraw",
            working_on_it=0,
            serial=data["serial"],
        )
        return ConversationHandler.END


async def back_from_decline_withdraw_order(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        data = update.callback_query.data

        send_withdraw_callback_data = {
            **data,
            "name": "send withdraw order",
        }

        decline_withdraw_callback_data = {
            **data,
            "name": "decline withdraw order",
        }
        payment_ok_buttons = [
            [
                InlineKeyboardButton(
                    text="إرسال الطلب⬅️", callback_data=send_withdraw_callback_data
                ),
                InlineKeyboardButton(
                    text="رفض طلب السحب❌",
                    callback_data=decline_withdraw_callback_data,
                ),
            ]
        ]
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(payment_ok_buttons)
        )
        return ConversationHandler.END


check_payment_handler = CallbackQueryHandler(
    callback=check_payment,
    pattern=lambda d: isinstance(d, dict) and d.get("name", False) == "check withdraw",
)

send_withdraw_order_handler = CallbackQueryHandler(
    callback=send_withdraw_order,
    pattern=lambda d: isinstance(d, dict)
    and d.get("name", False) == "send withdraw order",
)

decline_withdraw_order_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            callback=decline_withdraw_order,
            pattern=lambda d: isinstance(d, dict)
            and d.get("name", False) == "decline withdraw order",
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
            pattern=lambda d: isinstance(d, dict)
            and d.get("name", False) == "back from decline withdraw order",
        )
    ],
    name='decline_withdraw_order_handler',
    persistent=True,
)
