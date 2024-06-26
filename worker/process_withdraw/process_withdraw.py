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

from DB import DB
import os

from custom_filters import Withdraw, Returned

from common.common import (
    build_worker_keyboard,
)

RETURN_REASON = 0


async def user_payment_verified(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            order_type="withdraw",
        )

        await update.callback_query.answer(
            text="قم بالرد على هذه الرسالة بصورة لإشعار الدفع، في حال وجود مشكلة يمكنك إعادة الطلب مرفقاً برسالة.",
            show_alert=True,
        )

        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="إعادة الطلب📥",
                    callback_data=f"return_withdraw_order_{serial}",
                )
            )
        )


async def reply_with_payment_proof_withdraw(
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
        w_order = DB.get_one_order(order_type="withdraw", serial=serial)

        amount = w_order["amount"]
        user_id = w_order["user_id"]

        caption = (
            f"مبروك، تم تأكيد عملية سحب "
            f"<b>{amount}'</b> "
            "بنجاح✅\n\n"
            f"الرقم التسلسلي للطلب: <code>{serial}</code>"
        )

        try:
            await context.bot.send_photo(
                chat_id=user_id,
                photo=update.message.photo[-1],
                caption=caption,
            )
        except:
            pass

        text = update.message.reply_to_message.text_html.split("\n")
        text.insert(0, "تمت الموافقة✅")
        message = await context.bot.send_photo(
            chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
            photo=update.message.photo[-1],
            caption="\n".join(text),
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
            reply_markup=build_worker_keyboard(),
        )
        await DB.reply_with_payment_proof(
            order_type='withdraw',
            amount=amount,
            archive_message_ids=str(message.id),
            method=w_order['method'],
            serial=serial,
            worker_id=update.effective_user.id,
        )
        context.user_data["requested"] = False


async def return_withdraw_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
                    callback_data=f"back_from_return_withdraw_order_{serial}",
                )
            )
        )
        return RETURN_REASON


async def return_withdraw_order_reason(
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
        w_order = DB.get_one_order(order_type="withdraw", serial=serial)

        withdraw_code = w_order["withdraw_code"]
        user_id = w_order["user_id"]

        text = (
            f"تمت إعادة طلب السحب صاحب الكود: <b>{withdraw_code}$</b>❗️\n\n"
            "السبب:\n"
            f"<b>{update.message.text_html}</b>\n\n"
            "قم بالضغط على الزر أدناه وإرفاق المطلوب."
        )

        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=text,
                reply_markup=InlineKeyboardMarkup.from_button(
                    InlineKeyboardButton(
                        text="إرفاق المطلوب",
                        callback_data=f"handle_return_withdraw_{update.effective_chat.id}_{serial}",
                    )
                ),
            )
        except:
            pass

        text = update.message.reply_to_message.text_html.split("\n")
        text.insert(0, "تمت إعادة الطلب📥")
        text = "\n".join(text) + f"\n\nسبب الإعادة:\n<b>{update.message.text_html}</b>"
        message = await context.bot.send_message(
            chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
            text=text,
        )

        await context.bot.edit_message_reply_markup(
            chat_id=update.effective_chat.id,
            message_id=update.message.reply_to_message.id,
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="تمت إعادة الطلب📥",
                    callback_data="📥📥📥📥📥📥📥📥",
                ),
            ),
        )

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="تمت إعادة الطلب📥",
            reply_markup=build_worker_keyboard(),
        )
        await DB.return_order(
            order_type='withdraw',
            archive_message_ids=str(message.id),
            reason=update.message.text,
            serial=serial,
        )
        context.user_data["requested"] = False
        return ConversationHandler.END


async def back_from_return_withdraw_order(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
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
                    callback_data=f"return_withdraw_order_{serial}",
                )
            )
        )
        return ConversationHandler.END


user_payment_verified_handler = CallbackQueryHandler(
    callback=user_payment_verified,
    pattern="^verify_withdraw_order",
)

reply_with_payment_proof_withdraw_handler = MessageHandler(
    filters=filters.REPLY & filters.PHOTO & Withdraw(),
    callback=reply_with_payment_proof_withdraw,
)

return_withdraw_order_handler = CallbackQueryHandler(
    callback=return_withdraw_order,
    pattern="^return_withdraw_order",
)
return_withdraw_order_reason_handler = MessageHandler(
    filters=filters.REPLY & filters.TEXT & Withdraw() & Returned(),
    callback=return_withdraw_order_reason,
)
back_from_return_withdraw_order_handler = CallbackQueryHandler(
    callback=back_from_return_withdraw_order,
    pattern="^back_from_return_withdraw_order",
)
