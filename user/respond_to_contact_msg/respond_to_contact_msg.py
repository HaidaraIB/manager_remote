from telegram import (
    Update,
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    filters,
    MessageHandler,
)

import models
from common.common import build_back_button, make_conv_text, order_dict_en_to_ar

RESPONSE = range(1)


async def respond_to_contact_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        data = update.callback_query.data.split("_")
        serial = int(data[-1])
        order_type = data[-2]
        admin_id = int(data[-3])
        context.user_data["respond_to_contact_msg_serial"] = serial
        context.user_data["respond_to_contact_msg_order_type"] = order_type
        context.user_data["respond_to_contact_msg_admin_id"] = admin_id
        await update.callback_query.answer(
            "قم بإرسال ردك",
            show_alert=True,
        )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                *build_back_button("back_to_respond_to_contact_msg")
            )
        )
        context.user_data["effective_respond_to_contact_message_id"] = (
            update.effective_message.id
        )

        return RESPONSE


async def back_to_respond_to_contact_msg(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    serial = context.user_data["respond_to_contact_msg_serial"]
    order_type = context.user_data["respond_to_contact_msg_order_type"]
    admin_id = context.user_data["respond_to_contact_msg_admin_id"]
    if update.effective_chat.type == Chat.PRIVATE:

        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="إرسال رد",
                    callback_data=f"reply_to_contact_user_{admin_id}_{order_type}_{serial}",
                )
            )
        )
        return ConversationHandler.END


async def get_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        serial = context.user_data["respond_to_contact_msg_serial"]
        order_type = context.user_data["respond_to_contact_msg_order_type"]
        admin_id = context.user_data["respond_to_contact_msg_admin_id"]
        await models.ContactUserConv.add_response(
            admin_id=update.effective_user.id,
            from_user=True,
            msg=update.message.text_html,
            order_type=order_type,
            serial=serial,
        )
        conv = models.ContactUserConv.get_conv(order_type=order_type, serial=serial)
        msg = (
            make_conv_text(conv)
            + f"هذه الرسالة من المستخدم عن طلب <b>{order_dict_en_to_ar[order_type]}</b> ذي الرقم التسلسلي <code>{serial}</code>"
        )
        await context.bot.send_message(
            chat_id=admin_id,
            text=msg,
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="إرسال رد",
                    callback_data=f"contact_user_{order_type}_order_{serial}",
                )
            ),
        )
        await context.bot.edit_message_reply_markup(
            chat_id=update.effective_chat.id,
            message_id=context.user_data["effective_respond_to_contact_message_id"],
        )
        await update.message.reply_text(text="تم إرسال الرد ✅")
        return ConversationHandler.END


respond_to_contact_msg_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(respond_to_contact_msg, "^respond_to_contact_user")
    ],
    states={
        RESPONSE: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND, callback=get_response
            )
        ]
    },
    fallbacks=[
        CallbackQueryHandler(
            back_to_respond_to_contact_msg,
            "^back_to_respond_to_contact_msg$",
        ),
    ],
    persistent=True,
    name="respond_to_contact_msg_conv",
)
