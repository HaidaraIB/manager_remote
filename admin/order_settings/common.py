from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Chat
from telegram.ext import ContextTypes, ConversationHandler
from custom_filters import Admin
from common.common import parent_to_child_models_mapper
from common.back_to_home_page import back_to_admin_home_page_button
from common.stringifies import (
    general_stringify_order,
    order_settings_dict,
    state_dict_en_to_ar,
)


def build_order_types_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(
                text="سحب 💳",
                callback_data="withdraw_order#settings",
            )
        ],
        [
            InlineKeyboardButton(
                text="إيداع 📥",
                callback_data="deposit_order#settings",
            )
        ],
        [
            InlineKeyboardButton(
                text="شراء USDT 💰",
                callback_data="busdt_order#settings",
            )
        ],
    ]
    return keyboard


def build_actions_keyboard(order_type: str, serial: int):
    order = parent_to_child_models_mapper[order_type].get_one_order(serial=serial)
    actions_keyboard = [
        [
            InlineKeyboardButton(
                text="طلب الوثائق",
                callback_data=f"request_{order_type}_order_photos_{serial}",
            ),
            InlineKeyboardButton(
                text="تواصل مع المستخدم",
                callback_data=f"contact_user_{order_type}_order_{serial}",
            ),
        ],
    ]

    edit_amount_button = InlineKeyboardButton(
        text="تعديل المبلغ",
        callback_data=f"edit_{order_type}_order_amount_{serial}",
    )
    return_to_worker_button = InlineKeyboardButton(
        text="إعادة إلى الموظف المسؤول",
        callback_data=f"admin_return_{order_type}_order_{serial}",
    )
    request_returned_conv_button = InlineKeyboardButton(
        text="طلب محادثة إعادة",
        callback_data=f"request_{order_type}_order_returned_conv_{serial}",
    )
    delete_order_button = InlineKeyboardButton(
        text="حذف الطلب",
        callback_data=f"delete_{order_type}_order_{serial}",
    )
    unset_working_on_it_button = InlineKeyboardButton(
        text="السماح بإعادة الطلب",
        callback_data=f"unset_working_on_it_{order_type}_order_{serial}",
    )
    if order.state == "pending":
        actions_keyboard.append([])

    elif order.state in ["checking", "processing", "ignored"]:
        if order.state == "checking":
            actions_keyboard.append([])
        if order.working_on_it or order.state == "ignored":
            actions_keyboard.append([unset_working_on_it_button])

    elif order.state in ["declined", "sent", "approved"]:
        if order.state == "declined":
            actions_keyboard.append([])
        elif order.state == "approved":
            actions_keyboard[0].append(edit_amount_button)
            actions_keyboard.append([request_returned_conv_button])
        elif order.state == "sent":
            actions_keyboard[0].append(edit_amount_button)
            actions_keyboard.append([])
        actions_keyboard.append([return_to_worker_button])

    elif order.state == "returned":
        actions_keyboard.append([delete_order_button, request_returned_conv_button])

    actions_keyboard.append(back_to_admin_home_page_button[0])
    return actions_keyboard


def build_order_settings_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(
                text="استعلام عن طلب",
                callback_data="lookup_order",
            ),
            InlineKeyboardButton(text="عدد الطلبات", callback_data="count_orders"),
        ]
    ]
    return keyboard


def build_states_keyboard():
    keyboard: list[list[InlineKeyboardButton]] = []
    for i in range(0, len(state_dict_en_to_ar), 2):
        row = []
        row.append(
            InlineKeyboardButton(
                text=list(state_dict_en_to_ar.values())[i],
                callback_data=list(state_dict_en_to_ar.keys())[i],
            )
        )
        if i + 1 < len(state_dict_en_to_ar):
            row.append(
                InlineKeyboardButton(
                    text=list(state_dict_en_to_ar.values())[i + 1],
                    callback_data=list(state_dict_en_to_ar.keys())[i + 1],
                )
            )
        keyboard.append(row)
    return keyboard


async def back_to_choose_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        data = update.callback_query.data.split("_")
        serial = int(data[-1])
        order_type = data[-3]
        order = order_settings_dict[order_type]["cls"].get_one_order(serial=serial)
        actions_keyboard = build_actions_keyboard(order_type, serial)
        tg_user = await context.bot.get_chat(chat_id=order.user_id)
        await update.callback_query.edit_message_text(
            text=general_stringify_order(
                serial,
                order_type,
                "@" + tg_user.username if tg_user.username else tg_user.full_name,
            ),
            reply_markup=InlineKeyboardMarkup(actions_keyboard),
        )
        return ConversationHandler.END


async def refresh_order_settings_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    serial: int,
    order_type: str,
    note: str,
):
    order = parent_to_child_models_mapper[order_type].get_one_order(serial=serial)
    tg_user = await context.bot.get_chat(chat_id=order.user_id)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=general_stringify_order(
            serial,
            order_type,
            "@" + tg_user.username if tg_user.username else tg_user.full_name,
        )
        + note,
        reply_markup=InlineKeyboardMarkup(build_actions_keyboard(order_type, serial)),
    )
