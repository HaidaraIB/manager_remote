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
from models import BuyUsdtdOrder
from custom_filters import BuyUSDT, Declined, DepositAgent

from common.common import build_worker_keyboard, send_message_to_user
from common.stringifies import stringify_process_busdt_order


async def check_busdt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        serial = int(update.callback_query.data.split("_")[-1])

        payment_ok_buttons = [
            [
                InlineKeyboardButton(
                    text="إرسال الطلب⬅️", callback_data=f"send_busdt_order_{serial}"
                ),
                InlineKeyboardButton(
                    text="رفض الطلب❌", callback_data=f"decline_busdt_order_{serial}"
                ),
            ]
        ]
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(payment_ok_buttons),
        )


async def send_busdt_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:
        serial = int(update.callback_query.data.split("_")[-1])
        b_order = BuyUsdtdOrder.get_one_order(serial=serial)
        method = b_order.method

        target_group = f"{method}_group"

        amount = b_order.amount

        message = await context.bot.send_photo(
            chat_id=context.bot_data["data"][target_group],
            photo=update.effective_message.photo[-1],
            caption=stringify_process_busdt_order(
                amount=amount * context.bot_data["data"]["usdt_to_syp"],
                serial=serial,
                method=method,
                payment_method_number=b_order.payment_method_number,
            ),
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="قبول الطلب ✅", callback_data=f"verify_busdt_order_{serial}"
                )
            ),
        )

        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="تم إرسال الطلب✅",
                    callback_data="✅✅✅✅✅✅✅✅✅✅",
                )
            )
        )

        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text="تم إرسال الطلب✅",
            reply_markup=build_worker_keyboard(
                deposit_agent=DepositAgent().filter(update)
            ),
        )

        await BuyUsdtdOrder.send_order(
            pending_process_message_id=message.id,
            serial=serial,
            group_id=context.bot_data["data"][target_group],
            ex_rate=context.bot_data["data"]["usdt_to_syp"],
        )


async def decline_busdt_order(update: Update, _: ContextTypes.DEFAULT_TYPE):
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
                    callback_data=f"back_from_decline_busdt_order_{serial}",
                )
            )
        )


async def decline_busdt_order_reason(
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

        b_order = BuyUsdtdOrder.get_one_order(serial=serial)

        amount = b_order.amount

        text = (
            f"تم رفض عملية شراء <b>{amount} USDT</b>❗️\n\n"
            "السبب:\n"
            f"<b>{update.message.text_html}</b>\n\n"
            f"الرقم التسلسلي للطلب: <code>{serial}</code>"
        )
        await send_message_to_user(
            update=update,
            context=context,
            user_id=b_order.user_id,
            msg=text,
        )

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
                    text="تم رفض الطلب❌",
                    callback_data="❌❌❌❌❌❌❌",
                )
            ),
        )

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="تم رفض الطلب❌",
            reply_markup=build_worker_keyboard(
                deposit_agent=DepositAgent().filter(update)
            ),
        )
        await BuyUsdtdOrder.decline_order(
            reason=update.message.text,
            serial=serial,
        )


async def back_from_decline_busdt_order(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        serial = int(update.callback_query.data.split("_")[-1])

        payment_ok_buttons = [
            [
                InlineKeyboardButton(
                    text="إرسال الطلب⬅️", callback_data=f"send_busdt_order_{serial}"
                ),
                InlineKeyboardButton(
                    text="رفض الطلب❌", callback_data=f"decline_busdt_order_{serial}"
                ),
            ]
        ]
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(payment_ok_buttons)
        )


check_busdt_handler = CallbackQueryHandler(
    callback=check_busdt,
    pattern="^check_busdt",
)

send_busdt_order_handler = CallbackQueryHandler(
    callback=send_busdt_order,
    pattern="^send_busdt_order",
)

decline_busdt_order_handler = CallbackQueryHandler(
    callback=decline_busdt_order,
    pattern="^decline_busdt_order",
)
decline_busdt_order_reason_handler = MessageHandler(
    filters=filters.REPLY & filters.TEXT & BuyUSDT() & Declined(),
    callback=decline_busdt_order_reason,
)
back_from_decline_busdt_order_handler = CallbackQueryHandler(
    callback=back_from_decline_busdt_order,
    pattern="^back_from_decline_busdt_order",
)
