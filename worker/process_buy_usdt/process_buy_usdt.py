from telegram import (
    Chat,
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
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

from custom_filters import BuyUSDT, Returned

from common.common import (
    build_worker_keyboard,
)

RETURN_REASON = 0


async def user_payment_verified_buy_usdt(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        if update.effective_user.id in context.bot_data["suspended_workers"]:
            await update.callback_query.answer(
                "تم إيقافك عن العمل إلى حين معالجة الشكاوى الصادرة باسمك."
            )
            return

        serial = int(update.callback_query.data.split("_")[-1])

        await DB.add_order_worker_id(
            serial=serial,
            worker_id=update.effective_user.id,
            order_type="buy_usdt",
        )

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

        await DB.change_order_state(
            order_type="buy_usdt",
            serial=serial,
            state="approved",
        )

        b_order = DB.get_one_order(order_type="buy_usdt", serial=serial)

        amount = b_order["amount"]

        await DB.increment_worker_withdraws(
            worder_id=update.effective_user.id,
            method=b_order["method"],
        )
        await DB.update_worker_approved_withdraws(
            worder_id=update.effective_user.id,
            method=b_order["method"],
            amount=amount,
        )

        user_caption = (
            f"مبروك، تم تأكيد عملية شراء <b>{amount} USDT</b> بنجاح✅\n\n"
            f"الرقم التسلسلي للطلب: <code>{serial}</code>"
        )

        try:
            await context.bot.send_photo(
                chat_id=b_order["user_id"],
                photo=update.message.photo[-1],
                caption=user_caption,
            )
        except:
            pass

        media = [
            InputMediaPhoto(media=update.message.reply_to_message.photo[-1]),
            InputMediaPhoto(media=update.message.photo[-1]),
        ]

        caption = update.message.reply_to_message.caption_html.split("\n")
        caption.insert(0, "تمت الموافقة✅")
        messages = await context.bot.send_media_group(
            chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
            media=media,
            caption="\n".join(caption),
        )

        await DB.add_message_ids(
            serial=serial,
            archive_message_ids=f"{messages[0].id},{messages[1].id}",
            order_type="buy_usdt",
        )

        await context.bot.edit_message_reply_markup(
            chat_id=update.effective_chat.id,
            message_id=update.message.reply_to_message.id,
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="تمت الموافقة✅", callback_data="تمت الموافقة✅"
                ),
            ),
        )

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="تمت الموافقة✅",
            reply_markup=build_worker_keyboard(),
        )

        context.user_data["requested"] = False
        await DB.set_working_on_it(
            order_type="buy_usdt",
            working_on_it=0,
            serial=serial,
        )


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
        return RETURN_REASON


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

        await DB.change_order_state(
            order_type="buy_usdt",
            serial=serial,
            state="returned",
        )
        await DB.add_order_reason(
            order_type="buy_usdt",
            serial=serial,
            reason=update.message.text,
        )

        b_order = DB.get_one_order(
            order_type="buy_usdt",
            serial=serial,
        )

        amount = b_order["amount"]

        text = (
            f"تم إعادة طلب شراء: <b>{amount} USDT</b>❗️\n\n"
            "السبب:\n"
            f"<b>{update.message.text_html}</b>\n\n"
            "قم بالضغط على الزر أدناه وإرفاق المطلوب."
        )

        try:
            await context.bot.send_photo(
                chat_id=b_order["user_id"],
                photo=update.message.reply_to_message.photo[-1],
                caption=text,
                reply_markup=InlineKeyboardMarkup.from_button(
                    InlineKeyboardButton(
                        text="إرفاق المطلوب",
                        callback_data=f"return_buy_usdt_{update.effective_chat.id}_{serial}",
                    )
                ),
            )
        except:
            pass

        caption = update.message.reply_to_message.caption_html.split("\n")
        caption.insert(0, "تمت إعادة الطلب📥")
        caption = (
            "\n".join(caption) + f"\n\nسبب الإعادة:\n<b>{update.message.text_html}</b>"
        )
        message = await context.bot.send_photo(
            chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
            photo=update.message.reply_to_message.photo[-1],
            caption=caption,
        )

        await DB.add_message_ids(
            archive_message_ids=str(message.id),
            serial=serial,
            order_type="buy_usdt",
        )

        await context.bot.edit_message_reply_markup(
            chat_id=update.effective_chat.id,
            message_id=update.message.reply_to_message.id,
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="تمت إعادة الطلب📥", callback_data="تمت إعادة الطلب📥"
                )
            ),
        )

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="تمت إعادة الطلب📥",
            reply_markup=build_worker_keyboard(),
        )
        context.user_data["requested"] = False
        await DB.set_working_on_it(
            order_type="buy_usdt",
            working_on_it=0,
            serial=serial,
        )
        return ConversationHandler.END


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
        return ConversationHandler.END


user_payment_verified_buy_usdt_handler = CallbackQueryHandler(
    callback=user_payment_verified_buy_usdt,
    pattern="^verify_buy_usdt_order",
)

reply_with_payment_proof_buy_usdt_handler = MessageHandler(
    filters=filters.REPLY & filters.PHOTO & BuyUSDT(),
    callback=reply_with_payment_proof_buy_usdt,
)

return_buy_usdt_order_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            callback=return_buy_usdt_order,
            pattern="^return_buy_usdt_order",
        )
    ],
    states={
        RETURN_REASON: [
            MessageHandler(
                filters=filters.REPLY & filters.TEXT & BuyUSDT() & Returned(),
                callback=return_buy_usdt_order_reason,
            )
        ]
    },
    fallbacks=[
        CallbackQueryHandler(
            callback=back_from_return_buy_usdt_order,
            pattern="^back_from_return_buy_usdt_order",
        )
    ],
    name="return_buy_usdt_order_handler",
    persistent=True,
)
