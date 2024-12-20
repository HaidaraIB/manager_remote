from telegram import (
    Chat,
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
)
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
import os
import datetime
from models import BuyUsdtdOrder, ReturnedConv, Offer
from custom_filters import BuyUSDT, Returned, DepositAgent, Approved
from common.constants import *
from common.common import (
    build_worker_keyboard,
    pretty_time_delta,
    format_amount,
    send_to_photos_archive,
    send_photo_to_user,
    send_media_to_user,
)
from common.stringifies import create_order_user_info_line


async def user_payment_verified_busdt(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        serial = int(update.callback_query.data.split("_")[-1])
        order = BuyUsdtdOrder.get_one_order(serial=serial)
        if order.state == "deleted":
            button = InlineKeyboardButton(
                text="طلب محذوف ⁉️",
                callback_data="!?!?!?!?!?!?!?!?!?!?!?",
            )
            text = "لقد قامت الإدارة بحذف هذا الطلب ⁉️"
        else:
            button = InlineKeyboardButton(
                text="إعادة الطلب📥",
                callback_data=f"return_busdt_order_{serial}",
            )
            text = "قم بالرد على هذه الرسالة بصورة لإشعار الدفع، في حال وجود مشكلة يمكنك إعادة الطلب مرفقاً برسالة."

        await update.callback_query.answer(text=text, show_alert=True)
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(button)
        )


async def reply_with_payment_proof_busdt(
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

        user_caption = (
            f"مبروك، تم تأكيد عملية شراء <b>{format_amount(b_order.amount)} USDT</b> بنجاح ✅\n\n"
            + (
                f"مضافاً إليها مبلغ العرض 💥: <b>{format_amount(Offer.get(offer_id=b_order.offer).gift)}</b>\n"
                if b_order.offer
                else ""
            )
            + f"الرقم التسلسلي للطلب: <code>{serial}</code>"
        )

        media = [
            InputMediaPhoto(media=update.message.reply_to_message.photo[-1]),
            InputMediaPhoto(media=update.message.photo[-1]),
        ]

        await send_media_to_user(
            update=update,
            context=context,
            user_id=b_order.user_id,
            media=media,
            msg=user_caption,
        )

        caption = "تمت الموافقة ✅\n" + update.message.reply_to_message.caption_html

        await context.bot.send_media_group(
            chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
            media=media,
            caption=caption,
        )

        await context.bot.edit_message_reply_markup(
            chat_id=update.effective_chat.id,
            message_id=update.message.reply_to_message.id,
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text=APPROVED_TEXT,
                    callback_data=APPROVED_TEXT,
                ),
            ),
        )

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=APPROVED_TEXT,
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

        await BuyUsdtdOrder.approve_payment_order(
            amount=b_order.amount,
            method=b_order.method,
            serial=serial,
            worker_id=update.effective_user.id,
        )
        await send_to_photos_archive(
            context=context,
            photo=update.message.photo[-1],
            order_type="busdt",
            serial=serial,
        )


async def return_busdt_order(update: Update, _: ContextTypes.DEFAULT_TYPE):
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
                    callback_data=f"back_from_return_busdt_order_{serial}",
                )
            )
        )


async def return_busdt_order_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        reason = update.message.text_html

        await ReturnedConv.add_response(
            serial=serial,
            order_type="busdt",
            worker_id=update.effective_user.id,
            msg=reason,
            from_user=False,
        )

        text = (
            f"تمت إعادة طلب شراء: <b>{amount} USDT</b> ❗️\n\n"
            "السبب:\n"
            f"<b>{reason}</b>\n\n"
            "قم بالضغط على الزر أدناه وإرفاق المطلوب."
        )
        message = await send_photo_to_user(
            update=update,
            context=context,
            user_id=b_order.user_id,
            photo=update.message.reply_to_message.photo[-1],
            msg=text,
            keyboard=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="إرفاق المطلوب",
                    callback_data=f"handle_return_busdt_{update.effective_chat.id}_{serial}",
                )
            ),
        )
        if not message:
            res_flag = "لقد قام هذا المستخدم بحظر البوت"
        else:
            res_flag = "تمت إعادة الطلب 📥"
            await BuyUsdtdOrder.add_message_ids(
                serial=serial,
                returned_message_id=message.id,
            )

        order_user_info_line = await create_order_user_info_line(
            user_id=b_order.user_id, context=context
        )
        caption = (
            res_flag
            + "\n"
            + update.message.reply_to_message.caption_html
            + order_user_info_line
            + f"سبب الإعادة:\n<b>{reason}</b>"
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
                    text=res_flag,
                    callback_data="📥📥📥📥📥📥📥📥",
                )
            ),
        )

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=res_flag,
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
                photo=update.message.reply_to_message.photo[-1],
                caption=(
                    f"طلب متأخر بمقدار\n"
                    + f"<code>{pretty_time_delta(latency.total_seconds() - 600)}</code>\n"
                    f"الموظف المسؤول {update.effective_user.name}\n\n" + caption
                ),
            )

        await BuyUsdtdOrder.return_order_to_user(serial=serial)


async def back_from_return_busdt_order(update: Update, _: ContextTypes.DEFAULT_TYPE):
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
                    callback_data=f"return_busdt_order_{serial}",
                )
            )
        )


user_payment_verified_busdt_handler = CallbackQueryHandler(
    callback=user_payment_verified_busdt,
    pattern="^verify_busdt_order",
)

reply_with_payment_proof_busdt_handler = MessageHandler(
    filters=filters.REPLY & filters.PHOTO & BuyUSDT() & Approved(),
    callback=reply_with_payment_proof_busdt,
)

return_busdt_order_handler = CallbackQueryHandler(
    callback=return_busdt_order,
    pattern="^return_busdt_order",
)
return_busdt_order_reason_handler = MessageHandler(
    filters=filters.REPLY & filters.TEXT & BuyUSDT() & Returned(),
    callback=return_busdt_order_reason,
)
back_from_return_busdt_order_handler = CallbackQueryHandler(
    callback=back_from_return_busdt_order,
    pattern="^back_from_return_busdt_order",
)
