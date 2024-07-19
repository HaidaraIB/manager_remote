from telegram import (
    Chat,
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButtonRequestUsers,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from common.common import build_admin_keyboard, build_back_button

from common.back_to_home_page import (
    back_to_admin_home_page_button,
    back_to_admin_home_page_handler,
)

from start import admin_command

import os
from custom_filters import Admin
import database

(
    NEW_ADMIN_ID,
    CHOOSE_ADMIN_ID_TO_REMOVE,
) = range(2)

admin_settings_keyboard = [
    [
        InlineKeyboardButton(text="إضافة آدمن➕", callback_data="add admin"),
        InlineKeyboardButton(text="حذف آدمن✖️", callback_data="remove admin"),
    ],
    [
        InlineKeyboardButton(
            text="عرض آيديات الآدمنز الحاليين🆔", callback_data="show admins"
        )
    ],
    back_to_admin_home_page_button[0],
]


async def admin_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        await update.callback_query.edit_message_text(
            text="إعدادات الآدمن🪄",
            reply_markup=InlineKeyboardMarkup(admin_settings_keyboard),
        )


async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        await update.callback_query.answer()
        await update.callback_query.delete_message()
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text=(
                "اختر حساب الآدمن الذي تريد إضافته بالضغط على الزر أدناه\n\n"
                "يمكنك إلغاء العملية بالضغط على /admin."
            ),
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [
                        KeyboardButton(
                            text="اختيار حساب آدمن",
                            request_users=KeyboardButtonRequestUsers(
                                request_id=4, user_is_bot=False
                            ),
                        )
                    ]
                ],
                resize_keyboard=True,
            ),
        )
        return NEW_ADMIN_ID


async def new_admin_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        if update.effective_message.users_shared:
            admin_id = update.effective_message.users_shared.users[0].user_id
        else:
            admin_id = int(update.message.text)

        await database.Admin.add_new_admin(admin_id=admin_id)
        await update.message.reply_text(
            text="تمت إضافة الآدمن بنجاح✅.",
            reply_markup=ReplyKeyboardRemove(),
        )
        await update.message.reply_text(
            text="القائمة الرئيسية🔝",
            reply_markup=build_admin_keyboard(),
        )
        return ConversationHandler.END


async def remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        await update.callback_query.answer()
        admins = database.Admin.get_admin_ids()
        admin_ids_keyboard = [
            [InlineKeyboardButton(text=str(admin.id), callback_data=str(admin.id))]
            for admin in admins
        ]
        admin_ids_keyboard.append(build_back_button("back_to_admin_settings"))
        admin_ids_keyboard.append(back_to_admin_home_page_button[0])
        await update.callback_query.edit_message_text(
            text="اختر من القائمة أدناه id الآدمن الذي تريد إزالته.",
            reply_markup=InlineKeyboardMarkup(admin_ids_keyboard),
        )
        return CHOOSE_ADMIN_ID_TO_REMOVE


async def choose_admin_id_to_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        admin_id = int(update.callback_query.data)
        if admin_id == int(os.getenv("OWNER_ID")):
            await update.callback_query.answer(
                text="لا يمكنك إزالة مالك البوت من قائمة الآدمنز❗️",
                show_alert=True,
            )
            return

        await database.Admin.remove_admin(admin_id=admin_id)
        await update.callback_query.answer(text="تمت إزالة الآدمن بنجاح✅")
        admins = database.Admin.get_admin_ids()
        admin_ids_keyboard = [
            [InlineKeyboardButton(text=str(admin.id), callback_data=str(admin.id))]
            for admin in admins
        ]
        admin_ids_keyboard.append(build_back_button("back_to_admin_settings"))
        admin_ids_keyboard.append(back_to_admin_home_page_button[0])
        await update.callback_query.edit_message_text(
            text="اختر من القائمة أدناه id الآدمن الذي تريد إزالته.",
            reply_markup=InlineKeyboardMarkup(admin_ids_keyboard),
        )

        return CHOOSE_ADMIN_ID_TO_REMOVE


async def back_to_admin_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        await update.callback_query.edit_message_text(
            text="هل تريد:",
            reply_markup=InlineKeyboardMarkup(admin_settings_keyboard),
        )
        return ConversationHandler.END


async def show_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admins = database.Admin.get_admin_ids()
    text = "آيديات الآدمنز الحاليين:\n\n"
    for admin in admins:
        if admin.id == int(os.getenv("OWNER_ID")):
            text += "<code>" + str(admin.id) + "</code>" + " <b>مالك البوت</b>\n"
            continue
        text += "<code>" + str(admin.id) + "</code>" + "\n"
    text += "\nاختر ماذا تريد أن تفعل:"
    keyboard = build_admin_keyboard()
    await update.callback_query.edit_message_text(
        text=text,
        reply_markup=keyboard,
    )


admin_settings_handler = CallbackQueryHandler(
    admin_settings,
    "^admin settings$",
)

show_admins_handler = CallbackQueryHandler(
    callback=show_admins,
    pattern="^show admins$",
)

add_admin_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            callback=add_admin,
            pattern="^add admin$",
        ),
    ],
    states={
        NEW_ADMIN_ID: [
            MessageHandler(
                filters=filters.Regex("^\d+$"),
                callback=new_admin_id,
            ),
            MessageHandler(
                filters=filters.StatusUpdate.USERS_SHARED,
                callback=new_admin_id,
            ),
        ]
    },
    fallbacks=[
        CallbackQueryHandler(
            callback=back_to_admin_settings,
            pattern="^back_to_admin_settings$",
        ),
        admin_command,
        back_to_admin_home_page_handler,
    ],
)

remove_admin_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            callback=remove_admin,
            pattern="^remove admin$",
        ),
    ],
    states={
        CHOOSE_ADMIN_ID_TO_REMOVE: [
            CallbackQueryHandler(
                choose_admin_id_to_remove,
                "^\d+$",
            ),
        ]
    },
    fallbacks=[
        CallbackQueryHandler(
            callback=back_to_admin_settings,
            pattern="^back_to_admin_settings$",
        ),
        admin_command,
        back_to_admin_home_page_handler,
    ],
)
