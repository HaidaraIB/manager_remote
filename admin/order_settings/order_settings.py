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
from common.stringifies import state_dict_en_to_ar
from start import admin_command, start_command
from custom_filters import Admin
from admin.order_settings.common import (
    build_order_types_keyboard,
    build_order_settings_keyboard,
)
from admin.order_settings.lookup_order import lookup_order, get_serial, SERIAL
from admin.order_settings.count_orders import count_orders, STATE

(
    CHOOSE_ORDER_TYPE,
    CHOOSE_ORDER_SETTING,
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
        keyboard = [
            *build_order_settings_keyboard(),
            build_back_button("back_to_choose_order_type"),
            back_to_admin_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text="اختر:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return CHOOSE_ORDER_SETTING


back_to_choose_order_type = order_settings

back_to_choose_order_setting = choose_order_type

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
        CHOOSE_ORDER_SETTING: [
            CallbackQueryHandler(count_orders, "^count_orders$"),
            CallbackQueryHandler(lookup_order, "^lookup_order$"),
        ],
        SERIAL: [
            MessageHandler(
                filters=filters.Regex("^\d+$"),
                callback=get_serial,
            )
        ],
        STATE: [
            CallbackQueryHandler(
                count_orders,
                lambda x: x in state_dict_en_to_ar,
            )
        ],
    },
    fallbacks=[
        CallbackQueryHandler(back_to_choose_order_type, "^back_to_choose_order_type$"),
        CallbackQueryHandler(back_to_get_order_serial, "^back_to_get_order_serial$"),
        CallbackQueryHandler(
            back_to_choose_order_setting, "^back_to_choose_order_setting$"
        ),
        admin_command,
        start_command,
        back_to_admin_home_page_handler,
    ],
)
