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

        # if update.effective_user.id in context.bot_data["suspended_workers"]:
        #     await update.callback_query.answer(
        #         "تم إيقافك عن العمل إلى حين معالجة الشكاوى الصادرة باسمك."
        #     )
        #     return

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
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="إعادة الطلب📥", callback_data=f"return_deposit_order_{serial}"
                )
            )
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

        d_order = DB.get_one_order(order_type="deposit", serial=serial)

        user = DB.get_user(user_id=d_order["user_id"])

        gifts_amount = 0

        if user[3] >= 1_000_000:
            gifts_amount = 10_000 * context.bot_data["data"]["deposit_gift_percentage"]
            await DB.million_gift_user(user_id=d_order["user_id"], amount=gifts_amount)

        caption = (
            f"مبروك🎉، تم إضافة المبلغ الذي قمت بإيداعه <b>{d_order['amount']}$</b> إلى رصيدك\n"
            f"{f"بالإضافة إلى <b>{gifts_amount}$</b> مكافأة لوصول مجموع مبالغ إيداعاتك إلى\n<b>1_000_000$</b>" if gifts_amount else ''}\n\n"
            f"الرقم التسلسلي للطلب: <code>{serial}</code>\n"
            f"Congrats🎉, the deposit you made <b>{d_order['amount']}$</b> was added to your balance\n"
            f"{f"plus <b>{gifts_amount}$</b> gift for reaching <b>1_000_000$</b> deposits." if gifts_amount else ''}\n\n"
            f"Serial: <code>{serial}</code>"
        )
        await context.bot.send_photo(
            chat_id=d_order["user_id"],
            photo=update.message.photo[-1],
            caption=caption,
        )

        caption = update.message.reply_to_message.text_html.split("\n")
        caption.insert(0, "تمت الموافقة✅")

        message = await context.bot.send_photo(
            chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
            photo=update.message.photo[-1],
            caption="\n".join(caption),
        )

        await context.bot.edit_message_reply_markup(
            chat_id=update.effective_chat.id,
            message_id=update.message.reply_to_message.id,
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="تمت الموافقة✅",
                    callback_data="✅✅✅✅✅✅✅✅✅",
                )
            ),
        )

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="تمت الموافقة✅",
            reply_markup=build_worker_keyboard(),
        )

        await DB.reply_with_deposit_proof(
            order_type="deposit",
            amount=d_order["amount"],
            archive_message_ids=str(message.id),
            serial=serial,
            user_id=d_order["user_id"],
            worker_id=update.effective_user.id,
        )
        context.user_data["requested"] = False


async def return_deposit_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
                    callback_data=f"back_from_return_deposit_order_{serial}",
                )
            )
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
        ].callback_data.split("_")[-1]

        d_order = DB.get_one_order(order_type="deposit", serial=serial)

        caption = (
            f"تم إعادة طلب إيداع مبلغ: <b>{d_order['amount']}$</b>❗️\n\n"
            "السبب:\n"
            f"<b>{update.message.text_html}</b>\n\n"
            "قم بالضغط على الزر أدناه وإرفاق المطلوب."
        )

        await context.bot.send_photo(
            chat_id=d_order["user_id"],
            photo=update.message.reply_to_message.photo[-1],
            caption=caption,
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="إرفاق المطلوب",
                    callback_data=f"handle_return_deposit_{update.effective_chat.id}_{serial}",
                )
            ),
        )

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

        await context.bot.edit_message_reply_markup(
            chat_id=update.effective_chat.id,
            message_id=update.message.reply_to_message.id,
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="تمت إعادة الطلب📥", callback_data="📥📥📥📥📥📥📥📥"
                )
            ),
        )

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="تمت إعادة الطلب📥",
            reply_markup=build_worker_keyboard(),
        )

        await DB.return_order(
            order_type="deposit",
            archive_message_ids=str(message.id),
            reason=update.message.text,
            serial=serial,
        )

        context.user_data["requested"] = False
        return ConversationHandler.END


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
    filters=filters.REPLY & filters.PHOTO & Deposit(),
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
