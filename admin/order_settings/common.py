from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Chat,
)
from telegram.ext import ContextTypes, ConversationHandler
from common.common import (
    build_back_button,
    parent_to_child_models_mapper,
)
from common.back_to_home_page import back_to_admin_home_page_button
from common.stringifies import general_stringify_order, order_settings_dict


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
                text="تعديل المبلغ",
                callback_data=f"edit_{order_type}_order_amount_{serial}",
            ),
            InlineKeyboardButton(
                text="طلب الوثائق",
                callback_data=f"request_{order_type}_order_photos_{serial}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="إعادة إلى الموظف المسؤول",
                callback_data=f"admin_return_{order_type}_order_{serial}",
            ),
        ],
    ]
    unset_working_on_it_button = InlineKeyboardButton(
        text="السماح بإعادة الطلب",
        callback_data=f"unset_working_on_it_{order_type}_order_{serial}",
    )
    if order.working_on_it:
        actions_keyboard.append([unset_working_on_it_button])
    # send_order_button = InlineKeyboardButton(
    #     text="إرسال الطلب",
    #     callback_data=f"admin_send_{order_type}_order_{serial}",
    # )
    # decline_order_button = InlineKeyboardButton(
    #     text="رفض الطلب",
    #     callback_data=f"admin_decline_{order_type}_order_{serial}",
    # )
    # if order.state == "declined":
    #     actions_keyboard.append([send_order_button])
    # elif order.state == "sent":
    #     actions_keyboard.append([decline_order_button])
    # elif order.state == "pending":
    #     actions_keyboard.append([decline_order_button, send_order_button])
    # elif order.state == "approved":
    #     pass

    actions_keyboard.append(back_to_admin_home_page_button[0])
    return actions_keyboard


async def back_to_choose_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        serial = context.user_data["edit_order_amount_serial"]
        order_type = context.user_data["edit_order_amount_type"]
        order = order_settings_dict[order_type]["cls"].get_one_order(serial=serial)

        back_buttons = [
            build_back_button("back_to_get_serial"),
            back_to_admin_home_page_button[0],
        ]
        actions_keyboard = build_actions_keyboard(order_type, serial)
        actions_keyboard.append(back_buttons[0])
        actions_keyboard.append(back_buttons[1])
        tg_user = await context.bot.get_chat(chat_id=order.user_id)
        await update.message.reply_text(
            text=general_stringify_order(
                order,
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
