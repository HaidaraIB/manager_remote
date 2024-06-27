from telegram import (
    Update,
    Chat,
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

from custom_filters.User import User

from common.common import (
    build_user_keyboard,
    build_complaint_keyboard,
)

from common.back_to_home_page import back_to_user_home_page_handler

(
    CORRECT_RETURNED_WITHDRAW,
    CORRECT_RETURNED_DEPOSIT,
    CORRECT_RETURNED_BUY_USDT,
    CORRECT_RETURNED_COMPLAINT,
) = range(4)

from worker.check_buy_usdt import check_buy_usdt
from worker.check_deposit import check_deposit
from worker.check_withdraw import check_withdraw

from DB import DB


async def reply_to_returned_complaint(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        await update.callback_query.answer(
            text="قم بإرسال ردك، يمكنك إرسال صورة أو نص أو الاثنين معاً.",
            show_alert=True,
        )

        data = update.callback_query.data

        context.user_data["returned_complaint_data"] = data
        back_button_data = {
            **data,
            "name": "back from reply to returned complaint",
        }
        back_button = [
            [
                InlineKeyboardButton(
                    text="الرجوع عن الرد على الشكوى🔙", callback_data=back_button_data
                )
            ]
        ]
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(back_button)
        )

        return CORRECT_RETURNED_COMPLAINT


async def correct_returned_complaint(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):

        data = context.user_data["returned_complaint_data"]

        text_list = data["text"].split("\n")

        if update.message.text:
            text_list.insert(
                len(text_list), f"رد المستخدم على الشكوى:\n<b>{update.message.text}</b>"
            )
        elif update.message.caption:
            text_list.insert(
                len(text_list),
                f"رد المستخدم على الشكوى:\n<b>{update.message.caption}</b>",
            )

        data["text"] = "\n".join(text_list)

        chat_id = (
            data["op"]["worker_id"]
            if data["from_worker"]
            else context.bot_data["data"]["complaints_group"]
        )

        reply_markup = build_complaint_keyboard(data)

        if not update.message.photo:
            if data["media"]:
                await context.bot.send_media_group(
                    chat_id=chat_id,
                    media=[InputMediaPhoto(media=photo) for photo in data["media"]],
                    caption="\n".join(text_list),
                )
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"<b>ملحق بالشكوى على الطلب ذي الرقم التسلسلي {data['op']['serial']}</b>\n\nقم باختيار ماذا تريد أن تفعل⬇️",
                    reply_markup=reply_markup,
                )
            else:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="\n".join(text_list),
                    reply_markup=reply_markup,
                )
        else:
            photos = [update.message.photo[-1]]
            if data["media"]:
                photos = data["media"]
                photos.append(update.message.photo[-1])

            await context.bot.send_media_group(
                chat_id=chat_id,
                media=[InputMediaPhoto(media=photo) for photo in photos],
                caption="\n".join(text_list),
            )
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"<b>ملحق بالشكوى على الطلب ذي الرقم التسلسلي {data['op']['serial']}</b>\n\nقم باختيار ماذا تريد أن تفعل⬇️",
                reply_markup=reply_markup,
            )
        await update.message.reply_text(
            text="تم إرسال الرد✅",
        )
        return ConversationHandler.END


async def back_from_reply_to_returned_complaint(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        data = update.callback_query.data
        user_button_callback_data = {
            **data,
            "name": "user reply to complaint",
        }
        user_button = [
            [
                InlineKeyboardButton(
                    text="إرسال رد⬅️", callback_data=user_button_callback_data
                )
            ]
        ]
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(user_button),
        )
        return ConversationHandler.END


async def handle_returned_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        await update.callback_query.answer(text="قم بإرسال المطلوب في السبب.")
        await update.callback_query.edit_message_reply_markup()
        data = update.callback_query.data.split("_")
        context.user_data["return_to_chat_id"] = int(data[2])
        context.user_data["returned_withdraw_order_serial"] = int(data[3])
        return CORRECT_RETURNED_WITHDRAW


async def correct_returned_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        serial = context.user_data["returned_withdraw_order_serial"]
        w_order = DB.get_one_order(order_type="withdraw", serial=serial)
        await context.bot.send_message(
            chat_id=context.user_data["return_to_chat_id"],
            text=stringify_returned_order(
                update.message.text,
                check_withdraw.stringify_order,
                w_order["amount"],
                serial,
                w_order["method"],
                w_order["payment_method_number"],
            ),
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="قبول الطلب✅",
                    callback_data=f"verify_withdraw_order_{serial}",
                )
            ),
        )

        await update.message.reply_text(
            text="شكراً لك، تمت إعادة طلبك إلى قسم المراجعة، سيصلك رد خلال وقت قصير.",
            reply_markup=build_user_keyboard(),
        )
        return ConversationHandler.END


async def handle_returned_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        await update.callback_query.answer(text="قم بإرسال المطلوب في السبب.")
        await update.callback_query.edit_message_reply_markup()
        data = update.callback_query.data.split("_")
        context.user_data["return_to_chat_id_deposit"] = int(data[2])
        context.user_data["effective_photo"] = update.effective_message.photo[-1]
        context.user_data["returned_deposit_order_serial"] = int(data[3])
        return CORRECT_RETURNED_DEPOSIT


async def correct_returned_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        serial = context.user_data["returned_deposit_order_serial"]
        d_order = DB.get_one_order(order_type="deposit", serial=serial)
        await context.bot.send_photo(
            chat_id=context.user_data["return_to_chat_id_deposit"],
            photo=context.user_data["effective_photo"],
            caption=stringify_returned_order(
                update.message.text,
                check_deposit.stringify_order,
                d_order["amount"],
                d_order["method"],
                d_order["account_number"],
                serial,
            ),
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="قبول الطلب✅", callback_data=f"verify_deposit_order_{serial}"
                )
            ),
        )

        await update.message.reply_text(
            text="شكراً لك، تمت إعادة طلبك إلى قسم المراجعة، سيصلك رد خلال وقت قصير.",
            reply_markup=build_user_keyboard(),
        )
        return ConversationHandler.END


async def handle_returned_buy_usdt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        await update.callback_query.answer(text="قم بإرسال المطلوب في السبب.")
        await update.callback_query.edit_message_reply_markup()
        data = update.callback_query.data.split("_")
        context.user_data["return_to_chat_id_buy_usdt"] = int(data[3])
        context.user_data["effective_photo"] = update.effective_message.photo[-1]
        context.user_data["returned_buy_usdt_order_serial"] = int(data[4])
        return CORRECT_RETURNED_BUY_USDT


async def correct_returned_buy_usdt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        serial = context.user_data["returned_buy_usdt_order_serial"]
        b_order = DB.get_one_order(order_type="buy_usdt", serial=serial)
        await context.bot.send_photo(
            chat_id=context.user_data["return_to_chat_id_buy_usdt"],
            photo=context.user_data["effective_photo"],
            caption=stringify_returned_order(
                update.message.text,
                check_buy_usdt.stringify_order,
                b_order["amount"],
                serial,
                b_order["method"],
                b_order["payment_method_number"],
            ),
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="قبول الطلب✅",
                    callback_data=f"verify_buy_usdt_order_{serial}",
                )
            ),
        )

        await update.message.reply_text(
            text="شكراً لك، تمت إعادة طلبك إلى قسم المراجعة، سيصلك رد خلال وقت قصير.",
            reply_markup=build_user_keyboard(),
        )
        return ConversationHandler.END


def stringify_returned_order(attachments: str, stringify_order, *args):
    order = stringify_order(*args)
    order += "<b>" + "\n\nطلب معاد، المرفقات:\n\n" + attachments + "</b>"
    return order


handle_returned_deposit_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            handle_returned_deposit,
            "^return_deposit",
        )
    ],
    states={
        CORRECT_RETURNED_DEPOSIT: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=correct_returned_deposit,
            )
        ]
    },
    fallbacks=[back_to_user_home_page_handler],
)

handle_returned_withdraw_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            handle_returned_withdraw,
            "^return_withdraw",
        )
    ],
    states={
        CORRECT_RETURNED_WITHDRAW: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=correct_returned_withdraw,
            )
        ]
    },
    fallbacks=[back_to_user_home_page_handler],
)

handle_returned_buy_usdt_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            handle_returned_buy_usdt,
            "^return_buy_usdt",
        )
    ],
    states={
        CORRECT_RETURNED_BUY_USDT: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=correct_returned_buy_usdt,
            )
        ]
    },
    fallbacks=[back_to_user_home_page_handler],
)


reply_to_returned_complaint_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            reply_to_returned_complaint,
            lambda d: isinstance(d, dict) and d["name"] == "user reply to complaint",
        )
    ],
    states={
        CORRECT_RETURNED_COMPLAINT: [
            MessageHandler(
                filters=filters.TEXT
                & ~filters.COMMAND
                & (filters.CAPTION | filters.PHOTO | filters.TEXT),
                callback=correct_returned_complaint,
            )
        ]
    },
    fallbacks=[
        CallbackQueryHandler(
            back_from_reply_to_returned_complaint,
            lambda d: isinstance(d, dict)
            and d["name"] == "back from reply to returned complaint",
        ),
    ],
)
