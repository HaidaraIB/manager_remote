from telegram import Update, InlineKeyboardMarkup, Chat
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from common.common import build_back_button
from common.back_to_home_page import (
    back_to_admin_home_page_button,
    back_to_admin_home_page_handler,
)
from start import admin_command, start_command
from custom_filters import Admin
from admin.order_settings.common import (
    order_settings_dict,
    build_order_types_keyboard,
    general_stringify_order,
    build_actions_keyboard,
)

(
    CHOOSE_ORDER_TYPE,
    SERIAL,
) = range(2)


async def order_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        keyboard = build_order_types_keyboard()
        keyboard.append(back_to_admin_home_page_button[0])
        await update.callback_query.edit_message_text(
            text="إعدادات الطلبات",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return CHOOSE_ORDER_TYPE


async def choose_order_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        if not update.callback_query.data.startswith("back"):
            context.user_data["order_type_setting"] = update.callback_query.data.split(
                "#"
            )[0].replace("_order", "")
        back_buttons = [
            build_back_button("back_to_choose_order_type"),
            back_to_admin_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text="أرسل الرقم التسلسلي للطلب",
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return SERIAL


back_to_choose_order_type = order_settings


async def get_serial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        serial = int(update.message.text)
        order_type = context.user_data["order_type_setting"]
        order = order_settings_dict[order_type]["cls"].get_one_order(serial=serial)
        back_buttons = [
            build_back_button("back_to_get_order_serial"),
            back_to_admin_home_page_button[0],
        ]
        if not order:
            await update.message.reply_text(
                text="لم يتم العثور على الطلب، تأكد من الرقم التسلسلي وأعد المحاولة.",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
            return
        actions_keyboard = build_actions_keyboard(order_type, serial)
        tg_user = await context.bot.get_chat(chat_id=order.user_id)
        await update.message.reply_text(
            text=general_stringify_order(
                serial,
                order_type,
                "@" + tg_user.username if tg_user.username else tg_user.full_name,
            ),
            reply_markup=InlineKeyboardMarkup(actions_keyboard),
        )
        return ConversationHandler.END


back_to_get_order_serial = choose_order_type


order_settings_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            order_settings,
            "^order settings$",
        )
    ],
    states={
        CHOOSE_ORDER_TYPE: [
            CallbackQueryHandler(
                choose_order_type,
                "^.+order#settings$",
            )
        ],
        SERIAL: [
            MessageHandler(
                filters=filters.Regex("^\d+$"),
                callback=get_serial,
            )
        ],
    },
    fallbacks=[
        CallbackQueryHandler(back_to_choose_order_type, "^back_to_choose_order_type$"),
        CallbackQueryHandler(back_to_get_order_serial, "^back_to_get_order_serial$"),
        admin_command,
        start_command,
        back_to_admin_home_page_handler,
    ],
)
