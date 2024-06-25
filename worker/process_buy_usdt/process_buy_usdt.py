from telegram import (
    Chat,
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
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

from custom_filters import BuyUSDT, Returned, Declined

from common import (
    build_user_keyboard,
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

        data: dict = update.callback_query.data

        await DB.add_order_worker_id(
            serial=data["serial"],
            worker_id=update.effective_user.id,
            order_type="buy_usdt",
        )

        await update.callback_query.answer(
            text="قم بالرد على هذه الرسالة بصورة لإشعار الدفع، في حال وجود مشكلة يمكنك إعادة الطلب مرفقاً برسالة.",
            show_alert=True,
        )

        return_button_callback_data = {
            **data,
            "name": "return buy usdt order",
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
    media: list[InputMediaPhoto],
    caption: list,
    data: dict,
):
    await asyncio.sleep(after)
    messages = await context.bot.send_media_group(
        chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
        media=media,
        caption="\n".join(caption),
    )

    await DB.add_message_ids(
        serial=data["serial"],
        archive_message_ids=f"{messages[0].id},{messages[1].id}",
        order_type="buy_usdt",
    )


async def reply_with_payment_proof_buy_usdt(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        data = update.message.reply_to_message.reply_markup.inline_keyboard[0][
            0
        ].callback_data

        await DB.change_order_state(
            order_type="buy_usdt",
            serial=data["serial"],
            state="approved",
        )

        amount = data["amount"]

        await DB.increment_worker_withdraws(
            worder_id=update.effective_user.id,
            method=data["method"],
        )
        await DB.update_worker_approved_withdraws(
            worder_id=update.effective_user.id,
            method=data["method"],
            amount=amount,
        )

        user_caption = f"""مبروك، تم تأكيد عملية شراء <b>{amount} USDT</b> بنجاح✅
        
الرقم التسلسلي للطلب: <code>{data['serial']}</code>"""

        try:
            await context.bot.send_photo(
                chat_id=data["user_id"],
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
            serial=data["serial"],
            archive_message_ids=f"{messages[0].id},{messages[1].id}",
            order_type="buy_usdt",
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
            reply_markup=build_user_keyboard()
        )

        context.user_data["requested"] = False
        await DB.set_working_on_it(
            order_type="buy_usdt",
            working_on_it=0,
            serial=data["serial"],
        )


async def return_buy_usdt_order(update: Update, _: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        data: dict = update.callback_query.data

        back_from_return_callback_data = {
            **data,
            "name": "back from return buy usdt order",
        }
        return_buy_usdt_button = [
            [
                InlineKeyboardButton(
                    text="الرجوع عن الإعادة🔙",
                    callback_data=back_from_return_callback_data,
                )
            ],
        ]

        await update.callback_query.answer(
            text="قم بالرد على هذه الرسالة بسبب الإعادة", show_alert=True
        )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(return_buy_usdt_button)
        )
        return RETURN_REASON


async def archive_returned_usdt_after(
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
        archive_message_ids=str(message.id),
        serial=data["serial"],
        order_type="buy_usdt",
    )


async def return_buy_usdt_order_reason(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        data = update.message.reply_to_message.reply_markup.inline_keyboard[0][
            0
        ].callback_data

        await DB.change_order_state(
            order_type="buy_usdt",
            serial=data["serial"],
            state="returned",
        )
        await DB.add_order_reason(
            order_type="buy_usdt",
            serial=data["serial"],
            reason=update.message.text,
        )

        amount = data["amount"]

        text = f"""تم إعادة طلب شراء: <b>{amount} USDT</b>❗️

السبب:
<b>{update.message.text_html}</b>

قم بالضغط على الزر أدناه وإرفاق المطلوب."""

        attach_button = [
            [
                InlineKeyboardButton(
                    text="إرفاق المطلوب",
                    callback_data=[
                        "buy usdt",
                        update.effective_chat.id,
                        update.message.reply_to_message.caption_html,
                        data,
                    ],
                )
            ]
        ]
        try:
            await context.bot.send_photo(
                chat_id=data["user_id"],
                photo=update.message.reply_to_message.photo[-1],
                caption=text,
                reply_markup=InlineKeyboardMarkup(attach_button),
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
            serial=data["serial"],
            order_type="buy_usdt",
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
            reply_markup=build_user_keyboard(),
        )
        context.user_data["requested"] = False
        await DB.set_working_on_it(
            order_type="buy_usdt",
            working_on_it=0,
            serial=data["serial"],
        )
        return ConversationHandler.END


async def back_from_return_buy_usdt_order(update: Update, _: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        data: dict = update.callback_query.data

        return_button_callback_data = {
            **data,
            "name": "return buy usdt order",
            "worker_id": update.effective_user.id,
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


user_payment_verified_buy_usdt_handler = CallbackQueryHandler(
    callback=user_payment_verified_buy_usdt,
    pattern=lambda d: isinstance(d, dict)
    and d.get("name", False) == "verify buy usdt order",
)

reply_with_payment_proof_buy_usdt_handler = MessageHandler(
    filters=filters.REPLY & filters.PHOTO & BuyUSDT(),
    callback=reply_with_payment_proof_buy_usdt,
)

return_buy_usdt_order_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            callback=return_buy_usdt_order,
            pattern=lambda d: isinstance(d, dict)
            and d.get("name", False) == "return buy usdt order",
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
            pattern=lambda d: isinstance(d, dict)
            and d.get("name", False) == "back from return buy usdt order",
        )
    ],
    name='return_buy_usdt_order_handler',
    persistent=True,
)
