from telegram import (
    Chat,
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
)
from telegram.ext import ContextTypes, filters, CallbackQueryHandler, MessageHandler
from custom_filters import Deposit, Returned, DepositAgent, Approved
from models import DepositOrder, ReturnedConv
from common.common import (
    build_worker_keyboard,
    pretty_time_delta,
    format_amount,
    send_to_photos_archive,
    send_message_to_user,
    send_photo_to_user,
    send_media_to_user,
)
from common.stringifies import create_order_user_info_line
from common.constants import *
import datetime
import os


async def user_deposit_verified(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        serial = int(update.callback_query.data.split("_")[-1])

        order = DepositOrder.get_one_order(serial=serial)
        if order.state == "deleted":
            button = InlineKeyboardButton(
                text="طلب محذوف ⁉️",
                callback_data="!?!?!?!?!?!?!?!?!?!?!?",
            )
            text = "لقد قامت الإدارة بحذف هذا الطلب ⁉️"
        else:
            button = InlineKeyboardButton(
                text="إعادة الطلب📥",
                callback_data=f"return_deposit_order_{serial}",
            )
            text = "قم بالرد على هذه الرسالة بصورة لإشعار الشحن، في حال وجود مشكلة يمكنك إعادة الطلب مرفقاً برسالة."

        await update.callback_query.answer(text=text, show_alert=True)
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(button)
        )


async def reply_with_payment_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        serial = int(
            update.message.reply_to_message.reply_markup.inline_keyboard[0][
                0
            ].callback_data.split("_")[-1]
        )

        d_order = DepositOrder.get_one_order(serial=serial)

        caption = (
            "مبروك 🎉🎉🎉\n"
            f"تمت الموافقة على الإيداع بقيمة <b>{format_amount(d_order.amount)}</b>\n\n"
            f"الرقم التسلسلي للطلب: <code>{serial}</code>\n"
            f"وسيلة الدفع: <code>{d_order.method}</code>\n"
        )

        media = [
            InputMediaPhoto(update.message.photo[-1]),
        ]
        if update.message.reply_to_message.photo:
            media.append(InputMediaPhoto(update.message.reply_to_message.photo[-1]))

        await send_media_to_user(
            update=update,
            context=context,
            user_id=d_order.user_id,
            media=media,
            msg=caption,
        )

        caption = "تمت الموافقة ✅\n" + (
            update.message.reply_to_message.text_html
            if update.message.reply_to_message.text_html
            else update.message.reply_to_message.caption_html
        )
        order_user_info_line = await create_order_user_info_line(
            user_id=d_order.user_id, context=context
        )
        await context.bot.send_media_group(
            chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
            media=media,
            caption=caption + order_user_info_line,
        )

        await context.bot.edit_message_reply_markup(
            chat_id=update.effective_chat.id,
            message_id=update.message.reply_to_message.id,
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text=APPROVED_TEXT,
                    callback_data=APPROVED_TEXT,
                )
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
            d_order.send_date if d_order.state != "returned" else d_order.return_date
        )
        latency = datetime.datetime.now() - prev_date
        minutes, _ = divmod(latency.total_seconds(), 60)
        if minutes > 10:
            await context.bot.send_media_group(
                chat_id=context.bot_data["data"]["latency_group"],
                media=media,
                caption=f"طلب متأخر بمقدار\n"
                + f"<code>{pretty_time_delta(latency.total_seconds() - 600)}</code>\n"
                f"الموظف المسؤول {update.effective_user.name}\n\n" + caption,
            )

        await DepositOrder.approve_deposit_order(
            amount=d_order.amount,
            serial=serial,
            user_id=d_order.user_id,
            worker_id=update.effective_user.id,
        )
        await send_to_photos_archive(
            context=context,
            photo=update.message.photo[-1],
            order_type="deposit",
            serial=serial,
        )


async def return_deposit_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
                    callback_data=f"back_from_return_deposit_order_{serial}",
                )
            )
        )


async def return_deposit_order_reason(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        serial = update.message.reply_to_message.reply_markup.inline_keyboard[0][
            0
        ].callback_data.split("_")[-1]

        d_order = DepositOrder.get_one_order(serial=serial)
        reason = update.message.text_html

        await ReturnedConv.add_response(
            serial=serial,
            order_type="deposit",
            worker_id=update.effective_user.id,
            msg=reason,
            from_user=False,
        )

        user_text = (
            f"تم إعادة طلب إيداع مبلغ: <b>{d_order.amount}</b>❗️\n\n"
            "السبب:\n"
            f"<b>{reason}</b>\n\n"
            "قم بالضغط على الزر أدناه وإرفاق المطلوب."
        )

        order_user_info_line = await create_order_user_info_line(
            user_id=d_order.user_id, context=context
        )
        ar_text = (
            update.message.reply_to_message.text_html
            if update.message.reply_to_message.text_html
            else update.message.reply_to_message.caption
        ) + (order_user_info_line + f"سبب الإعادة:\n<b>{reason}</b>")

        return_button = InlineKeyboardButton(
            text="إرفاق المطلوب",
            callback_data=f"handle_return_deposit_{update.effective_chat.id}_{serial}",
        )

        if update.message.reply_to_message.photo:
            message = await send_photo_to_user(
                update=update,
                context=context,
                user_id=d_order.user_id,
                photo=update.message.reply_to_message.photo[-1],
                msg=user_text,
                keyboard=InlineKeyboardMarkup.from_button(return_button),
            )
        else:
            message = await send_message_to_user(
                update=update,
                context=context,
                user_id=d_order.user_id,
                msg=user_text,
                keyboard=InlineKeyboardMarkup.from_button(return_button),
            )

        if not message:
            res_flag = "لقد قام هذا المستخدم بحظر البوت"
        else:
            res_flag = "تمت إعادة الطلب 📥"
            await DepositOrder.add_message_ids(
                serial=serial,
                returned_message_id=message.id,
            )

        if update.message.reply_to_message.photo:
            await context.bot.send_photo(
                chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
                photo=update.message.reply_to_message.photo[-1],
                caption=res_flag + "\n" + ar_text,
            )
        else:
            await context.bot.send_message(
                chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
                text=res_flag + "\n" + ar_text,
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
            d_order.send_date if d_order.state != "returned" else d_order.return_date
        )
        latency = datetime.datetime.now() - prev_date
        minutes, _ = divmod(latency.total_seconds(), 60)
        if minutes > 10:
            if update.message.reply_to_message.text_html:
                await context.bot.send_message(
                    chat_id=context.bot_data["data"]["latency_group"],
                    text=f"طلب متأخر بمقدار\n"
                    + f"<code>{pretty_time_delta(latency.total_seconds() - 600)}</code>\n"
                    f"الموظف المسؤول {update.effective_user.name}\n\n" + ar_text,
                )
            else:
                await context.bot.send_photo(
                    chat_id=context.bot_data["data"]["latency_group"],
                    photo=update.message.reply_to_message.photo[-1],
                    caption=f"طلب متأخر بمقدار\n"
                    + f"<code>{pretty_time_delta(latency.total_seconds() - 600)}</code>\n"
                    f"الموظف المسؤول {update.effective_user.name}\n\n" + ar_text,
                )

        await DepositOrder.return_order_to_user(serial=serial)


async def back_from_return_deposit_order(update: Update, _: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        serial = int(update.callback_query.data.split("_")[-1])
        await update.callback_query.answer(
            text="قم بالرد على هذه الرسالة بصورة لإشعار الشحن، في حال وجود مشكلة يمكنك إعادة الطلب مرفقاً برسالة.",
            show_alert=True,
        )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="إعادة الطلب📥",
                    callback_data=f"return_deposit_order_{serial}",
                )
            )
        )


user_deposit_verified_handler = CallbackQueryHandler(
    callback=user_deposit_verified,
    pattern="^verify_deposit_order",
)


reply_with_payment_proof_handler = MessageHandler(
    filters=filters.REPLY & filters.PHOTO & Deposit() & Approved(),
    callback=reply_with_payment_proof,
)


return_deposit_order_handler = CallbackQueryHandler(
    callback=return_deposit_order,
    pattern="^return_deposit_order",
)
return_deposit_order_reason_handler = MessageHandler(
    filters=filters.REPLY & filters.TEXT & Deposit() & Returned(),
    callback=return_deposit_order_reason,
)
back_from_return_deposit_order_handler = CallbackQueryHandler(
    callback=back_from_return_deposit_order,
    pattern="^back_from_return_deposit_order",
)
