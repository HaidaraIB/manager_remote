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

import os
from DB import DB

from custom_filters import BuyUSDT, Declined

from common.common import (
    build_worker_keyboard,
)

DECLINE_REASON = 0


async def check_buy_usdt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        # if update.effective_user.id in context.bot_data['suspended_workers']:
        #     await update.callback_query.answer("تم إيقافك عن العمل إلى حين معالجة الشكاوى الصادرة باسمك.")
        #     return

        serial = int(update.callback_query.data.split("_")[-1])

        await DB.add_checker_id(
            order_type="buy_usdt",
            serial=serial,
            checker_id=update.effective_user.id,
        )

        payment_ok_buttons = [
            [
                InlineKeyboardButton(
                    text="إرسال الطلب⬅️", callback_data=f"send_buy_usdt_order_{serial}"
                ),
                InlineKeyboardButton(
                    text="رفض الطلب❌", callback_data=f"decline_buy_usdt_order_{serial}"
                ),
            ]
        ]
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(payment_ok_buttons),
        )


async def send_buy_usdt_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:
        serial = int(update.callback_query.data.split("_")[-1])
        b_order = DB.get_one_order(order_type="buy_usdt", serial=serial)
        method = b_order["method"]

        chat_id = f"{method}_group"

        amount = b_order["amount"]
        text = (
            update.effective_message.caption_html
            + "\n\n<b>تنبيه: اضغط على المعلومات لنسخها كما هي في الرسالة تفادياً للخطأ.</b>"
        ).split("\n")
        text[2] = (
            f"المبلغ💵: <code>{amount * context.bot_data['data']['usdt_to_syp']}</code> SYP"
        )
        del text[3]
        message = await context.bot.send_photo(
            chat_id=context.bot_data["data"][chat_id],
            photo=update.effective_message.photo[-1],
            caption="\n".join(text),
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="قبول الطلب✅", callback_data=f"verify_buy_usdt_order_{serial}"
                )
            ),
        )

        await DB.change_order_state(
            order_type="buy_usdt",
            serial=serial,
            state="sent",
        )
        await DB.add_message_ids(
            serial=serial,
            order_type="buy_usdt",
            pending_process_message_id=message.id,
        )

        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="تم إرسال الطلب✅",
                    callback_data="تم إرسال الطلب✅",
                )
            )
        )

        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text="تم إرسال الطلب✅",
            reply_markup=build_worker_keyboard,
        )

        context.user_data["requested"] = False
        await DB.set_working_on_it(
            order_type="buy_usdt",
            working_on_it=0,
            serial=serial,
        )


async def decline_buy_usdt_order(update: Update, _: ContextTypes.DEFAULT_TYPE):
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
                    callback_data=f"back_from_decline_buy_usdt_order_{serial}",
                )
            )
        )
        return DECLINE_REASON


async def decline_buy_usdt_order_reason(
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

        await DB.change_order_state(
            order_type="buy_usdt",
            serial=serial,
            state="declined",
        )
        await DB.add_order_reason(
            order_type="buy_usdt",
            serial=serial,
            reason=update.message.text,
        )

        b_order = DB.get_one_order(order_type="buy_usdt", serial=serial)

        amount = b_order["amount"]

        text = (
            f"تم رفض عملية شراء <b>{amount} USDT</b>❗️\n\n"
            "السبب:\n"
            f"<b>{update.message.text_html}</b>\n\n"
            f"الرقم التسلسلي للطلب: <code>{serial}</code>"
        )
        try:
            await context.bot.send_message(chat_id=b_order["user_id"], text=text)
        except:
            pass

        caption = update.message.reply_to_message.caption_html.split("\n")
        caption.insert(0, "تم رفض الطلب❌")
        caption = "\n".join(caption) + f"\n\nالسبب:\n<b>{update.message.text_html}</b>"
        message = await context.bot.send_photo(
            chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
            photo=update.message.reply_to_message.photo[-1],
            caption=caption,
        )

        await DB.add_message_ids(
            order_type="buy_usdt",
            archive_message_ids=str(message.id),
            serial=serial,
        )

        await context.bot.edit_message_reply_markup(
            chat_id=update.effective_chat.id,
            message_id=update.message.reply_to_message.id,
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="تم رفض الطلب❌", callback_data="تم رفض الطلب❌"
                )
            ),
        )

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="تم رفض الطلب❌",
            reply_markup=build_worker_keyboard(),
        )
        context.user_data["requested"] = False
        await DB.set_working_on_it(
            order_type="buy_usdt",
            working_on_it=0,
            serial=serial,
        )
        return ConversationHandler.END


async def back_from_decline_buy_usdt_order(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP]:

        serial = int(update.callback_query.data.split("_")[-1])

        payment_ok_buttons = [
            [
                InlineKeyboardButton(
                    text="إرسال الطلب⬅️", callback_data=f"send_buy_usdt_order_{serial}"
                ),
                InlineKeyboardButton(
                    text="رفض الطلب❌", callback_data=f"decline_buy_usdt_order_{serial}"
                ),
            ]
        ]
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(payment_ok_buttons)
        )
        return ConversationHandler.END


check_buy_usdt_handler = CallbackQueryHandler(
    callback=check_buy_usdt,
    pattern="^check_buy_usdt",
)

send_buy_usdt_order_handler = CallbackQueryHandler(
    callback=send_buy_usdt_order,
    pattern="^send_buy_usdt_order",
)

decline_buy_usdt_order_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            callback=decline_buy_usdt_order,
            pattern="^decline_buy_usdt_order",
        )
    ],
    states={
        DECLINE_REASON: [
            MessageHandler(
                filters=filters.REPLY & filters.TEXT & BuyUSDT() & Declined(),
                callback=decline_buy_usdt_order_reason,
            )
        ]
    },
    fallbacks=[
        CallbackQueryHandler(
            callback=back_from_decline_buy_usdt_order,
            pattern="^back_from_decline_buy_usdt_order",
        )
    ],
    name="decline_buy_usdt_order_handler",
    persistent=True,
)
