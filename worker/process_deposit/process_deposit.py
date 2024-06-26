from telegram import (
    Chat,
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
)
from telegram.ext import (
    ContextTypes,
    filters,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
)

import asyncio

from DB import DB
import os

from custom_filters import Deposit, Returned

from common.common import (
    build_worker_keyboard,
)

RETURN_REASON = 0


async def user_deposit_verified(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            order_type="deposit",
        )

        await update.callback_query.answer(
            text="قم بالرد على هذه الرسالة بصورة لإشعار الشحن، في حال وجود مشكلة يمكنك إعادة الطلب مرفقاً برسالة.",
            show_alert=True,
        )
        return_button = [
            [
                InlineKeyboardButton(
                    text="إعادة الطلب📥", callback_data=f"return_deposit_order_{serial}"
                )
            ]
        ]

        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(return_button)
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

        await DB.change_order_state(
            order_type="deposit", serial=serial, state="approved"
        )
        d_order = DB.get_one_order(order_type="deposit", serial=serial)

        await DB.update_balance(user_id=d_order["user_id"], amount=d_order["amount"])
        await DB.update_worker_approved_deposits(
            worder_id=update.effective_user.id, amount=d_order["amount"]
        )
        await DB.increment_worker_deposits(worder_id=update.effective_user.id)

        user = DB.get_user(user_id=d_order["user_id"])

        gifts_amount = 0

        if user[3] >= 1_000_000:
            gifts_amount = 10_000 * context.bot_data["data"]["deposit_gift_percentage"]
            await DB.million_gift_user(user_id=d_order["user_id"], amount=gifts_amount)

        caption = (f"مبروك🎉، تم إضافة المبلغ الذي قمت بإيداعه <b>{d_order['amount']}$</b> إلى رصيدك\n"
                   f"{f"بالإضافة إلى <b>{gifts_amount}$</b> مكافأة لوصول مجموع مبالغ إيداعاتك إلى\n<b>1_000_000$</b>" if gifts_amount else ''}\n\n"
                   f"الرقم التسلسلي للطلب: <code>{serial}</code>\n"
                   f"Congrats🎉, the deposit you made <b>{d_order['amount']}$</b> was added to your balance\n"
                   f"{f"plus <b>{gifts_amount}$</b> gift for reaching <b>1_000_000$</b> deposits." if gifts_amount else ''}\n\n"
                   f"Serial: <code>{serial}</code>")
        try:
            await context.bot.send_photo(
                chat_id=d_order["user_id"],
                photo=update.message.photo[-1],
                caption=caption,
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
            archive_message_ids=f"{messages[0].id},{messages[1].id}",
            serial=serial,
            order_type="deposit",
        )

        await context.bot.edit_message_reply_markup(
            chat_id=update.effective_chat.id,
            message_id=update.message.reply_to_message.id,
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="تمت الموافقة✅", callback_data="تمت الموافقة✅"
                )
            ),
        )

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="تمت الموافقة✅",
            reply_markup=build_worker_keyboard(),
        )

        await DB.set_working_on_it(
            order_type="deposit",
            working_on_it=0,
            serial=serial,
        )
        context.user_data["requested"] = False


async def return_deposit_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        serial = int(update.callback_query.data.split('_')[-1])
        back_from_deposit_button = [
            [
                InlineKeyboardButton(
                    text="الرجوع عن الإعادة🔙",
                    callback_data=f"back_from_return_deposit_order_{serial}",
                )
            ],
        ]

        await update.callback_query.answer(
            text="قم بالرد على هذه الرسالة بسبب الإعادة", show_alert=True
        )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(back_from_deposit_button)
        )

        return RETURN_REASON


async def return_deposit_order_reason(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        serial = update.message.reply_to_message.reply_markup.inline_keyboard[0][
            0
        ].callback_data.split('_')[-1]

        await DB.change_order_state(
            order_type="deposit",
            serial=serial,
            state="returned",
        )
        await DB.add_order_reason(
            order_type="deposit",
            serial=serial,
            reason=update.message.text,
        )

        d_order = DB.get_one_order(order_type='deposit', serial=serial)

        caption = (f"تم إعادة طلب إيداع مبلغ: <b>{d_order['amount']}$</b>❗️\n\n"
                   "السبب:\n"
                   f"<b>{update.message.text_html}</b>\n\n"
                   "قم بالضغط على الزر أدناه وإرفاق المطلوب."
                   )

        attach_button = [
            [
                InlineKeyboardButton(
                    text="إرفاق المطلوب",
                    callback_data=[
                        "deposit",
                        update.effective_chat.id,
                        update.message.reply_to_message.caption_html,
                        serial,
                    ],
                )
            ]
        ]

        try:
            await context.bot.send_photo(
                chat_id=d_order["user_id"],
                photo=update.message.reply_to_message.photo[-1],
                caption=caption,
                reply_markup=InlineKeyboardMarkup(attach_button),
            )
        except:
            pass

        caption = update.message.reply_to_message.caption.split("\n")
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
            order_type="deposit",
        )

        await context.bot.edit_message_reply_markup(
            chat_id=update.effective_chat.id,
            message_id=update.message.reply_to_message.id,
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(text="تمت إعادة الطلب📥", callback_data="تمت إعادة الطلب📥")
            )
        )

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="تمت إعادة الطلب📥",
            reply_markup=build_worker_keyboard(),
        )
        await DB.set_working_on_it(
            order_type="deposit",
            working_on_it=0,
            serial=serial,
        )
        context.user_data["requested"] = False
        return ConversationHandler.END


async def back_from_return_deposit_order(update: Update, _: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        serial = int(update.callback_query.data.split("_")[-1])

        return_button = [
            [
                InlineKeyboardButton(
                    text="إعادة الطلب📥", callback_data=f"return_deposit_order_{serial}"
                )
            ]
        ]
        await update.callback_query.answer(
            text="قم بالرد على هذه الرسالة بصورة لإشعار الشحن، في حال وجود مشكلة يمكنك إعادة الطلب مرفقاً برسالة.",
            show_alert=True,
        )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(return_button)
        )


user_deposit_verified_handler = CallbackQueryHandler(
    callback=user_deposit_verified,
    pattern="^verify_deposit_order",
)


reply_with_payment_proof_handler = MessageHandler(
    filters=filters.REPLY & filters.PHOTO & Deposit(),
    callback=reply_with_payment_proof,
)


return_deposit_order_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            callback=return_deposit_order,
            pattern="^return_deposit_order",
        )
    ],
    states={
        RETURN_REASON: [
            MessageHandler(
                filters=filters.REPLY & filters.TEXT & Deposit() & Returned(),
                callback=return_deposit_order_reason,
            )
        ]
    },
    fallbacks=[
        CallbackQueryHandler(
            callback=back_from_return_deposit_order,
            pattern="^back_from_return_deposit_order",
        )
    ],
    name="return_deposit_order_handler",
    persistent=True,
)
