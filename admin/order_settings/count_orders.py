from telegram import Update, Chat, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from custom_filters import Admin

from admin.order_settings.common import build_states_keyboard
from common.common import build_back_button, parent_to_child_models_mapper
from common.back_to_home_page import back_to_admin_home_page_button
from common.stringifies import state_dict_en_to_ar, order_settings_dict

STATE = 3


async def count_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        orders_count_text = ""
        if update.callback_query.data == "count_orders":
            context.user_data["order_setting"] = update.callback_query.data
        elif update.callback_query.data in state_dict_en_to_ar:
            state = update.callback_query.data
            order_type = context.user_data["order_type_setting"]
            context.user_data["count_orders_state"] = state
            count = parent_to_child_models_mapper[order_type].count_orders(state=state)
            orders_count_text = f"<b>{order_settings_dict[order_type]['t']} {state_dict_en_to_ar[state]}</b>، عدد الطلبات: <b>{count}</b>\n\n"

        keybaord = [
            *build_states_keyboard(),
            build_back_button("back_to_choose_order_setting"),
            back_to_admin_home_page_button[0],
        ]
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text=orders_count_text + "اختر حالة الطلب",
            reply_markup=InlineKeyboardMarkup(keybaord),
        )
        return STATE
