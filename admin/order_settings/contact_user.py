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

from custom_filters import Admin

from common.common import (
    parent_to_child_models_mapper,
    order_dict_en_to_ar,
    send_message_to_user,
    make_conv_text,
)
from admin.order_settings.common import back_to_choose_action
import models

CONTACT_USER_MESSAGE = 0


async def contact_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        data = update.callback_query.data.split("_")
        order_type = data[-3]
        serial = int(data[-1])
        context.user_data["serial_user_to_contact"] = serial
        context.user_data["order_type_user_to_contact"] = order_type
        await update.callback_query.answer(
            text="أرسل ما تود إرساله إلى المستخدم",
            show_alert=True,
        )

        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="الرجوع عن التواصل مع المستخدم 🔙",
                    callback_data=f"back_from_contact_user_{order_type}_order_{serial}",
                )
            )
        )
        return CONTACT_USER_MESSAGE


async def get_contact_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        serial = context.user_data["serial_user_to_contact"]
        order_type = context.user_data["order_type_user_to_contact"]
        order = parent_to_child_models_mapper[order_type].get_one_order(serial=serial)
        await models.ContactUserConv.add_response(
            admin_id=update.effective_user.id,
            from_user=False,
            msg=update.message.text_html,
            order_type=order_type,
            serial=serial,
        )
        conv = models.ContactUserConv.get_conv(order_type=order_type, serial=serial)
        msg = (
            make_conv_text(conv)
            + f"هذه الرسالة من الدعم عن طلب <b>{order_dict_en_to_ar[order_type]}</b> ذي الرقم التسلسلي <code>{serial}</code>"
        )
        res = await send_message_to_user(
            update,
            context,
            order.user_id,
            msg,
            InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="إرسال رد",
                    callback_data=f"respond_to_contact_user_{update.effective_user.id}_{order_type}_{serial}",
                )
            ),
        )
        if res:
            await update.message.reply_text(text="تم إرسال الرد ✅")
        return ConversationHandler.END


contact_user_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(contact_user, "^contact_user")],
    states={
        CONTACT_USER_MESSAGE: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=get_contact_user_message,
            )
        ]
    },
    fallbacks=[
        CallbackQueryHandler(
            back_to_choose_action,
            "^back_from_contact_user",
        ),
    ],
)
