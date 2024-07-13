from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Chat,
)

from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from user.work_with_us.common import syrian_govs_en_ar

from DB import DB


async def accept_agent_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        serial = update.callback_query.data.split("_")[-1]
        await update.callback_query.answer(
            text=(
                "قم بالرد على هذه الرسالة بتطبيق ال apk، ثم عدّل رسالة التطبيق مضيفاً إلى الكابشن معلومات تسجيل الدخول."
            ),
            show_alert=True,
        )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="الرجوع عن قبول الطلب 🔙",
                    callback_data=f"back_from_accept_trusted_agent_order_{update.effective_user.id}_{serial}",
                )
            )
        )


async def get_apk_login_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        if not update.edited_message:
            return
        data = update.edited_message.reply_to_message.reply_markup.inline_keyboard[0][
            0
        ].callback_data.split("_")
        manager_id = int(data[-2])

        if update.effective_user.id != manager_id:
            return

        serial = int(data[-1])
        order = DB.get_one_order(order_type="trusted_agents", serial=serial)

        await DB.add_trusted_agent(
            user_id=order["user_id"],
            order_serial=serial,
            gov=order["gov"],
        )
        await context.bot.send_message(
            chat_id=order["user_id"],
            text=(
                f"مبروك، تمت الموافقة على طلبك للعمل معنا كوكيل لمحافظة <b>{syrian_govs_en_ar[order['gov']]}</b>\n\n"
                "سيظهر زر يؤدي إلى حسابك الشخصي بين قائمة الوكلاء الموصى بهم في محافظتك من الآن فصاعداً.\n\n"
                f"الرقم التسلسلي للطلب: <code>{serial}</code>"
            ),
        )
        await context.bot.send_document(
            chat_id=order["user_id"],
            document=update.edited_message.document,
            caption=update.edited_message.caption,
        )
        await update.edited_message.reply_to_message.edit_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="تمت الموافقة ✅", callback_data="تمت الموافقة ✅"
                )
            )
        )


accept_agent_order_handler = CallbackQueryHandler(
    accept_agent_order, "^accept_agent_order_\d+$"
)

get_apk_login_info_handler = MessageHandler(
    filters=filters.Document.APK & filters.CAPTION, callback=get_apk_login_info
)
