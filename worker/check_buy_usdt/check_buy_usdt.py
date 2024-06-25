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

import os
from DB import DB
import asyncio

from custom_filters import BuyUSDT, Declined

from common import (
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

        data: dict = update.callback_query.data

        await DB.add_checker_id(
            order_type="buy_usdt",
            serial=data["serial"],
            checker_id=update.effective_user.id,
        )

        data_dict = {
            **data,
            "worker_id": update.effective_user.id,
        }
        send_order_callback_data = {
            **data_dict,
            "name": "send buy usdt order",
        }
        decline_order_callback_data = {
            **data_dict,
            "name": "decline buy usdt order",
        }
        payment_ok_buttons = [
            [
                InlineKeyboardButton(
                    text="إرسال الطلب⬅️", callback_data=send_order_callback_data
                ),
                InlineKeyboardButton(
                    text="رفض الطلب❌", callback_data=decline_order_callback_data
                ),
            ]
        ]
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(payment_ok_buttons),
        )


async def send_buy_usdt_order_after(
    after: int,
    context: ContextTypes.DEFAULT_TYPE,
    agent_id: int,
    update: Update,
    text: str,
    verify_button: list[list[InlineKeyboardButton]],
    data: dict,
):
    await asyncio.sleep(after)
    message = await context.bot.send_photo(
        chat_id=agent_id,
        photo=update.callback_query.message.photo[-1],
        caption="\n".join(text),
        reply_markup=InlineKeyboardMarkup(verify_button),
    )

    await DB.change_order_state(
        order_type="buy_usdt",
        serial=data["serial"],
        state="sent",
    )
    await DB.add_message_ids(
        serial=data["serial"],
        order_type="buy_usdt",
        pending_process_message_id=message.id,
    )


async def send_buy_usdt_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        data = update.callback_query.data

        method = data["method"]

        chat_id = f"{method}_group"

        verify_button_callback_data = {
            **data,
            "name": "verify buy usdt order",
        }

        verify_button = [
            [
                InlineKeyboardButton(
                    text="قبول الطلب✅", callback_data=verify_button_callback_data
                )
            ]
        ]

        amount = data["amount"]
        text = (
            update.callback_query.message.caption_html
            + "\n\n<b>تنبيه: اضغط على المعلومات لنسخها كما هي في الرسالة تفادياً للخطأ.</b>"
        ).split("\n")
        text[2] = (
            f"المبلغ💵: <code>{amount * context.bot_data['data']['usdt_to_syp']}</code> SYP"
        )
        del text[3]
        message = await context.bot.send_photo(
            chat_id=context.bot_data["data"][chat_id],
            photo=update.callback_query.message.photo[-1],
            caption="\n".join(text),
            reply_markup=InlineKeyboardMarkup(verify_button),
        )

        await DB.change_order_state(
            order_type="buy_usdt",
            serial=data["serial"],
            state="sent",
        )
        await DB.add_message_ids(
            serial=data["serial"],
            order_type="buy_usdt",
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
            reply_markup=build_worker_keyboard,
        )

        context.user_data["requested"] = False
        await DB.set_working_on_it(
            order_type="buy_usdt",
            working_on_it=0,
            serial=data["serial"],
        )


async def decline_buy_usdt_order(update: Update, _: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        data: dict = update.callback_query.data

        back_button_callback_data = {
            **data,
            "name": "back from decline buy usdt order",
        }
        decline_buy_usdt_button = [
            [
                InlineKeyboardButton(
                    text="الرجوع عن الرفض🔙",
                    callback_data=back_button_callback_data,
                )
            ],
        ]

        await update.callback_query.answer(
            text="قم بالرد على هذه الرسالة بسبب الرفض",
            show_alert=True,
        )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(decline_buy_usdt_button)
        )
        return DECLINE_REASON


async def archive_declined_usdt_after(
    after: int,
    context: ContextTypes.DEFAULT_TYPE,
    update: Update,
    caption: str,
    data: dict,
):
    await asyncio.sleep(after)
    message = await context.bot.send_photo(
        chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
        photo=update.message.reply_to_message.photo[-1],
        caption=caption,
    )
    await DB.add_message_ids(
        order_type="buy_usdt",
        archive_message_ids=str(message.id),
        serial=data["serial"],
    )


async def decline_buy_usdt_order_reason(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        data = update.message.reply_to_message.reply_markup.inline_keyboard[0][
            0
        ].callback_data

        serial = data["serial"]
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

        amount = data["amount"]

        text = f"""تم رفض عملية شراء <b>{amount} USDT</b>❗️

السبب:
<b>{update.message.text_html}</b>

الرقم التسلسلي للطلب: <code>{data['serial']}</code>
"""
        try:
            await context.bot.send_message(
                chat_id=data["user_id"], text=text
            )
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
            reply_markup=build_worker_keyboard(),
        )
        context.user_data["requested"] = False
        await DB.set_working_on_it(
            order_type="buy_usdt",
            working_on_it=0,
            serial=data["serial"],
        )
        return ConversationHandler.END


async def back_from_decline_buy_usdt_order(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP]:

        data: dict = update.callback_query.data

        send_order_callback_data = {
            **data,
            "name": "send buy usdt order",
        }
        decline_order_callback_data = {
            **data,
            "name": "decline buy usdt order",
        }
        payment_ok_buttons = [
            [
                InlineKeyboardButton(
                    text="إرسال الطلب⬅️", callback_data=send_order_callback_data
                ),
                InlineKeyboardButton(
                    text="رفض الطلب❌", callback_data=decline_order_callback_data
                ),
            ]
        ]
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(payment_ok_buttons)
        )
        return ConversationHandler.END


check_buy_usdt_handler = CallbackQueryHandler(
    callback=check_buy_usdt,
    pattern=lambda d: isinstance(d, dict) and d.get("name", False) == "check buy usdt",
)

send_buy_usdt_order_handler = CallbackQueryHandler(
    callback=send_buy_usdt_order,
    pattern=lambda d: isinstance(d, dict)
    and d.get("name", False) == "send buy usdt order",
)

decline_buy_usdt_order_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            callback=decline_buy_usdt_order,
            pattern=lambda d: isinstance(d, dict)
            and d.get("name", False) == "decline buy usdt order",
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
            pattern=lambda d: isinstance(d, dict)
            and d.get("name", False) == "back from decline buy usdt order",
        )
    ],
    name='decline_buy_usdt_order_handler',
    persistent=True,
)
