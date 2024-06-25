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

from DB import DB
import asyncio
import os

from custom_filters import Withdraw, Returned

from common import (
    build_worker_keyboard,
)

RETURN_REASON = 0


async def user_payment_verified(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        if update.effective_user.id in context.bot_data["suspended_workers"]:
            await update.callback_query.answer(
                "تم إيقافك عن العمل إلى حين معالجة الشكاوى الصادرة باسمك."
            )
            return

        data = update.callback_query.data

        await DB.add_order_worker_id(
            serial=data["serial"],
            worker_id=update.effective_user.id,
            order_type="withdraw",
        )

        await update.callback_query.answer(
            text="قم بالرد على هذه الرسالة بصورة لإشعار الدفع، في حال وجود مشكلة يمكنك إعادة الطلب مرفقاً برسالة.",
            show_alert=True,
        )

        return_button_callback_data = {
            **data,
            "name": "return withdraw order",
            "worker_id": update.effective_user.id,
        }
        return_button = [
            [
                InlineKeyboardButton(
                    text="إعادة الطلب📥", callback_data=return_button_callback_data
                )
            ]
        ]

        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(return_button)
        )


async def reply_with_proof_after(
    after: int,
    context: ContextTypes.DEFAULT_TYPE,
    update: Update,
    text: list,
    data: dict,
):
    await asyncio.sleep(after)
    message = await context.bot.send_photo(
        chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
        photo=update.message.photo[-1],
        caption="\n".join(text),
    )

    await DB.add_message_ids(
        archive_message_ids=str(message.id),
        serial=data["serial"],
        order_type="withdraw",
    )


async def reply_with_payment_proof_withdraw(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        data = update.message.reply_to_message.reply_markup.inline_keyboard[0][
            0
        ].callback_data

        await DB.change_order_state(
            order_type="withdraw", serial=data["serial"], state="approved"
        )

        amount = data["amount"]
        user_id = data["user_id"]

        await DB.increment_worker_withdraws(
            worder_id=update.effective_user.id,
            method=data["method"],
        )
        await DB.update_worker_approved_withdraws(
            worder_id=update.effective_user.id,
            method=data["method"],
            amount=amount,
        )

        caption = f"""مبروك، تم تأكيد عملية سحب <b>{f'مكافأة {amount}' if update.message.reply_to_message.text.startswith(
            "تفاصيل طلب سحب مكافأة") else f'{amount}'}$</b> بنجاح✅
            
الرقم التسلسلي للطلب: <code>{data['serial']}</code>
"""

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

        await DB.add_message_ids(
            archive_message_ids=str(message.id),
            serial=data["serial"],
            order_type="withdraw",
        )

        await context.bot.edit_message_reply_markup(
            chat_id=update.effective_chat.id,
            message_id=update.message.reply_to_message.id,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(text="تمت الموافقة✅", callback_data="تمت الموافقة✅"),
                ]
            ])
        )

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="تمت الموافقة✅",
            reply_markup=build_worker_keyboard()
        )
        await DB.set_working_on_it(
            order_type="withdraw",
            working_on_it=0,
            serial=data["serial"],
        )
        context.user_data["requested"] = False


async def return_withdraw_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        data = update.callback_query.data

        back_button_callback_data = {
            **data,
            "name": "back from return withdraw order",
        }
        return_withdraw_button = [
            [
                InlineKeyboardButton(
                    text="الرجوع عن الإعادة🔙",
                    callback_data=back_button_callback_data,
                )
            ],
        ]

        await update.callback_query.answer(
            text="قم بالرد على هذه الرسالة بسبب الإعادة",
            show_alert=True,
        )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(return_withdraw_button)
        )
        return RETURN_REASON


async def archive_returned_after(
    after: int, context: ContextTypes.DEFAULT_TYPE, text: str, data: dict
):
    message = await context.bot.send_message(
        chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
        text=text,
    )

    await DB.add_message_ids(
        archive_message_ids=str(message.id),
        serial=data["serial"],
        order_type="withdraw",
    )


async def return_withdraw_order_reason(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        data = update.message.reply_to_message.reply_markup.inline_keyboard[0][
            0
        ].callback_data

        await DB.change_order_state(
            order_type="withdraw", serial=data["serial"], state="returned"
        )
        await DB.add_order_reason(
            order_type="withdraw",
            serial=data["serial"],
            reason=update.message.text,
        )

        amount = data["amount"]
        user_id = data["user_id"]

        if update.message.reply_to_message.text.split("\n")[0].startswith(
            "تفاصيل طلب سحب مكافأة"
        ):
            await DB.update_gifts_balance(user_id=user_id, amount=amount)

        text = f"""تم إعادة طلب سحب مبلغ: <b>{amount}$</b>❗️

السبب:
<b>{update.message.text_html}</b>

قم بالضغط على الزر أدناه وإرفاق المطلوب."""

        attach_button = [
            [
                InlineKeyboardButton(
                    text="إرفاق المطلوب",
                    callback_data=[
                        "withdraw",
                        update.effective_chat.id,
                        update.message.reply_to_message.text_html,
                        data,
                    ],
                )
            ]
        ]

        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=text,
                reply_markup=InlineKeyboardMarkup(attach_button),
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

        await DB.add_message_ids(
            archive_message_ids=str(message.id),
            serial=data["serial"],
            order_type="withdraw",
        )
            
        await context.bot.edit_message_reply_markup(
            chat_id=update.effective_chat.id,
            message_id=update.message.reply_to_message.id,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(text="تمت إعادة الطلب📥", callback_data="تمت إعادة الطلب📥"),
                ]
            ])
        )

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="تمت إعادة الطلب📥",
            reply_markup=build_worker_keyboard(),
        )
        await DB.set_working_on_it(
            order_type="withdraw",
            working_on_it=0,
            serial=data["serial"],
        )
        context.user_data["requested"] = False
        return ConversationHandler.END


async def back_from_return_withdraw_order(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        data = update.callback_query.data

        return_button_callback_data = {
            **data,
            "name": "return withdraw order",
        }
        return_button = [
            [
                InlineKeyboardButton(
                    text="إعادة الطلب📥", callback_data=return_button_callback_data
                )
            ]
        ]
        await update.callback_query.answer(
            text="قم بالرد على هذه الرسالة بصورة لإشعار الدفع، في حال وجود مشكلة يمكنك إعادة الطلب مرفقاً برسالة.",
            show_alert=True,
        )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(return_button)
        )
        return ConversationHandler.END


user_payment_verified_handler = CallbackQueryHandler(
    callback=user_payment_verified,
    pattern=lambda d: isinstance(d, dict)
    and d.get("name", False) == "verify withdraw order",
)

reply_with_payment_proof_withdraw_handler = MessageHandler(
    filters=filters.REPLY & filters.PHOTO & Withdraw(),
    callback=reply_with_payment_proof_withdraw,
)

return_withdraw_order_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            callback=return_withdraw_order,
            pattern=lambda d: isinstance(d, dict)
            and d.get("name", False) == "return withdraw order",
        )
    ],
    states={
        RETURN_REASON: [
            MessageHandler(
                filters=filters.REPLY & filters.TEXT & Withdraw() & Returned(),
                callback=return_withdraw_order_reason,
            )
        ]
    },
    fallbacks=[
        CallbackQueryHandler(
            callback=back_from_return_withdraw_order,
            pattern=lambda d: isinstance(d, dict)
            and d.get("name", False) == "back from return withdraw order",
        )
    ],
    name='return_withdraw_order_handler',
    persistent=True,
)
