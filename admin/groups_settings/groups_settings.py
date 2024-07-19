from telegram import (
    Chat,
    Update,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButtonRequestChat,
    KeyboardButton,
)

from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from common.common import (
    build_admin_keyboard,
    build_groups_keyboard,
    check_hidden_keyboard,
)

from common.back_to_home_page import (
    back_to_admin_home_page_handler,
    back_to_admin_home_page_button,
)

from start import admin_command, start_command

from custom_filters.Admin import Admin

NEW_GROUP_ID = 0


async def change_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        change_groups_keyboard = [
            *build_groups_keyboard(op="change"),
            back_to_admin_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text="اختر الغروب الذي تريد تغييره:",
            reply_markup=InlineKeyboardMarkup(change_groups_keyboard),
        )


async def change_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        target_group = update.callback_query.data.replace("change ", "")
        context.user_data["target_group"] = target_group
        try:
            context.bot_data["data"][target_group]
        except KeyError:
            context.bot_data["data"][target_group] = -1002029384320
        await update.callback_query.delete_message()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=(
                f"الغروب الحالي: <code>{context.bot_data['data'][target_group]}</code>\n\n"
                "اختر الغروب الذي تريد تعديله بالضغط على الزر أدناه، يمكنك إلغاء العملية بالضغط على /admin."
            ),
            reply_markup=ReplyKeyboardMarkup.from_button(
                KeyboardButton(
                    text="اختيار غروب جديد 👥",
                    request_chat=KeyboardButtonRequestChat(
                        request_id=5,
                        chat_is_channel=False,
                    ),
                ),
                resize_keyboard=True,
            ),
        )
        return NEW_GROUP_ID


async def get_new_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        context.bot_data["data"][context.user_data["target_group"]] = (
            update.effective_message.chat_shared.chat_id
            if update.effective_message.chat_shared
            else int(update.message.text)
        )
        await update.message.reply_text(
            text="تم تعديل الغروب بنجاح✅",
            reply_markup=check_hidden_keyboard(context),
        )
        await update.message.reply_text(
            text="القائمة الرئيسية🔝",
            reply_markup=build_admin_keyboard(),
        )
        return ConversationHandler.END


change_groups_handler = CallbackQueryHandler(change_groups, "^change groups$")

change_group_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            change_group,
            "^change.*_group$",
        ),
    ],
    states={
        NEW_GROUP_ID: [
            MessageHandler(
                filters=filters.StatusUpdate.CHAT_SHARED,
                callback=get_new_group,
            ),
            MessageHandler(
                filters=filters.Regex("^-?\d+$"),
                callback=get_new_group,
            ),
        ]
    },
    fallbacks=[
        back_to_admin_home_page_handler,
        admin_command,
        start_command,
    ],
)
