from telegram import (
    Chat,
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
)

from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

import os
import datetime
from models import BuyUsdtdOrder
from custom_filters import BuyUSDT, Returned, DepositAgent

from common.common import (
    build_worker_keyboard,
    pretty_time_delta,
    format_amount,
    send_to_photos_archive,
)


async def user_payment_verified_buy_usdt(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        # if update.effective_user.id in context.bot_data["suspended_workers"]:
        #     await update.callback_query.answer(
        #         "تم إيقافك عن العمل إلى حين معالجة الشكاوى الصادرة باسمك."
        #     )
        #     return

        serial = int(update.callback_query.data.split("_")[-1])

        await update.callback_query.answer(
            text="قم بالرد على هذه الرسالة بصورة لإشعار الدفع، في حال وجود مشكلة يمكنك إعادة الطلب مرفقاً برسالة.",
            show_alert=True,
        )

        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="إعادة الطلب📥",
                    callback_data=f"return_buy_usdt_order_{serial}",
                )
            )
        )


async def reply_with_payment_proof_buy_usdt(
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

        user_caption = (
            f"مبروك، تم تأكيد عملية شراء <b>{format_amount(amount)} USDT</b> بنجاح ✅\n\n"
            f"الرقم التسلسلي للطلب: <code>{serial}</code>"
        )

        try:
            await context.bot.send_photo(
                chat_id=b_order.user_id,
                photo=update.message.photo[-1],
                caption=user_caption,
            )
        except:
            pass

        media = [
            InputMediaPhoto(media=update.message.reply_to_message.photo[-1]),
            InputMediaPhoto(media=update.message.photo[-1]),
        ]

        caption = "تمت الموافقة✅\n" + update.message.reply_to_message.caption_html

        messages = await context.bot.send_media_group(
            chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
            media=media,
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
            b_order.send_date if b_order.state != "returned" else b_order.return_date
        )
        latency = datetime.datetime.now() - prev_date
        minutes, _ = divmod(latency.total_seconds(), 60)
        if minutes > 10:
            await context.bot.send_media_group(
                chat_id=context.bot_data["data"]["latency_group"],
                media=media,
                caption=f"طلب متأخر بمقدار\n<code>{pretty_time_delta(latency.total_seconds() - 600)}</code>\n\n"
                + caption,
            )

        await BuyUsdtdOrder.reply_with_payment_proof(
            archive_message_ids=f"{messages[0].id},{messages[1].id}",
            amount=amount,
            method=b_order.method,
            serial=serial,
            worker_id=update.effective_user.id,
        )
        await send_to_photos_archive(
            context=context,
            photo=update.message.photo[-1],
            order_type="buy_usdt",
            serial=serial,
        )
        context.user_data["requested"] = False


async def return_buy_usdt_order(update: Update, _: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        serial = int(update.callback_query.data.split("_")[-1])

        await update.callback_query.answer(
            text="قم بالرد على هذه الرسالة بسبب الإعادة", show_alert=True
        )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="الرجوع عن الإعادة🔙",
                    callback_data=f"back_from_return_buy_usdt_order_{serial}",
                )
            )
        )


async def return_buy_usdt_order_reason(
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

        b_order = BuyUsdtdOrder.get_one_order(
            serial=serial,
        )

        amount = b_order.amount

        text = (
            f"تم إعادة طلب شراء: <b>{amount} USDT</b>❗️\n\n"
            "السبب:\n"
            f"<b>{update.message.text_html}</b>\n\n"
            "قم بالضغط على الزر أدناه وإرفاق المطلوب."
        )

        await context.bot.send_photo(
            chat_id=b_order.user_id,
            photo=update.message.reply_to_message.photo[-1],
            caption=text,
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="إرفاق المطلوب",
                    callback_data=f"handle_return_busdt_{update.effective_chat.id}_{serial}",
                )
            ),
        )

        caption = (
            "تمت إعادة الطلب📥\n"
            + update.message.reply_to_message.caption_html
            + f"\n\nسبب الإعادة:\n<b>{update.message.text_html}</b>"
        )

        message = await context.bot.send_photo(
            chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
            photo=update.message.reply_to_message.photo[-1],
            caption=caption,
        )

        await context.bot.edit_message_reply_markup(
            chat_id=update.effective_chat.id,
            message_id=update.message.reply_to_message.id,
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="تمت إعادة الطلب📥",
                    callback_data="📥📥📥📥📥📥📥📥",
                )
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
            b_order.send_date if b_order.state != "returned" else b_order.return_date
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

        await BuyUsdtdOrder.return_order(
            archive_message_ids=str(message.id),
            reason=update.message.text,
            serial=serial,
        )
        await send_to_photos_archive(
            context=context,
            photo=update.message.photo[-1],
            order_type="buy_usdt",
            serial=serial,
        )
        context.user_data["requested"] = False


async def back_from_return_buy_usdt_order(update: Update, _: ContextTypes.DEFAULT_TYPE):
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
                    callback_data=f"return_buy_usdt_order_{serial}",
                )
            )
        )


user_payment_verified_buy_usdt_handler = CallbackQueryHandler(
    callback=user_payment_verified_buy_usdt,
    pattern="^verify_buy_usdt_order",
)

reply_with_payment_proof_buy_usdt_handler = MessageHandler(
    filters=filters.REPLY & filters.PHOTO & BuyUSDT(),
    callback=reply_with_payment_proof_buy_usdt,
)

return_buy_usdt_order_handler = CallbackQueryHandler(
    callback=return_buy_usdt_order,
    pattern="^return_buy_usdt_order",
)
return_buy_usdt_order_reason_handler = MessageHandler(
    filters=filters.REPLY & filters.TEXT & BuyUSDT() & Returned(),
    callback=return_buy_usdt_order_reason,
)
back_from_return_buy_usdt_order_handler = CallbackQueryHandler(
    callback=back_from_return_buy_usdt_order,
    pattern="^back_from_return_buy_usdt_order",
)
