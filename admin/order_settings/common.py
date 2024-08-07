from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Chat,
)
from telegram.ext import ContextTypes, ConversationHandler
from models import (
    WithdrawOrder,
    DepositOrder,
    CreateAccountOrder,
    BuyUsdtdOrder,
)
from user.complaint.common import state_dict_en_to_ar
from common.common import (
    format_amount,
    build_back_button,
    parent_to_child_models_mapper,
)
from common.back_to_home_page import back_to_admin_home_page_button

from datetime import datetime
from dateutil import tz


def format_datetime(d: datetime):
    return d.replace(tzinfo=tz.gettz("Syria/Damascus")).strftime(r"%d/%m/%Y  %I:%M %p")


order_settings_dict: dict[
    str, dict[str, WithdrawOrder | DepositOrder | BuyUsdtdOrder | CreateAccountOrder]
] = {
    "withdraw": {"cls": WithdrawOrder, "t": "سحب"},
    "deposit": {"cls": DepositOrder, "t": "إيداع"},
    "busdt": {"cls": BuyUsdtdOrder, "t": "شراء USDT"},
}


def stringify_order(serial: int, order_type: str, name: str):
    order = parent_to_child_models_mapper[order_type].get_one_order(serial=serial)
    return (
        f"تفاصيل الطلب:\n\n"
        f"الرقم التسلسلي: <code>{order.serial}</code>\n\n"
        f"آيدي المستخدم صاحب الطلب: <code>{order.user_id}</code>\n"
        f"اسمه: <b>{name}</b>\n\n"
        f"نوع الطلب: <b>{order_settings_dict[order_type]['t']}</b>\n"
        f"المبلغ: <code>{format_amount(order.amount)}</code>\n"
        f"رقم الحساب: <code>{getattr(order, 'acc_number', 'لا يوجد')}</code>\n\n"
        f"وسيلة الدفع: <code>{order.method}</code>\n"
        f"محفظة الإيداع: <code>{getattr(order, 'deposit_wallet', 'لا يوجد')}</code>\n\n"
        f"الحالة: <b>{state_dict_en_to_ar[order.state]}</b>\n"
        f"سبب إعادة/رفض: <b>{'\n' + order.reason if order.reason else 'لا يوجد'}</b>\n\n"
        f"جاري العمل عليه: <b>{'نعم' if order.working_on_it else 'لا'}</b>\n"
        f"تم إغلاق شكوى عنه : <b>{'نعم' if order.complaint_took_care_of else 'لا'}</b>\n\n"
        f"تاريخ الإنشاء:\n<b>{format_datetime(order.order_date)}</b>\n\n"
        f"تاريخ الإرسال: <b>{'\n' + format_datetime(order.send_date) if order.send_date else 'لا يوجد'}</b>\n\n"
        f"تاريخ الموافقة: <b>{'\n' + format_datetime(order.approve_date) if order.approve_date else 'لا يوجد'}</b>\n\n"
        f"تاريخ الرفض: <b>{'\n' + format_datetime(order.decline_date) if order.decline_date else 'لا يوجد'}</b>\n\n"
        f"تاريخ الإعادة: <b>{'\n' + format_datetime(order.return_date) if order.return_date else 'لا يوجد'}</b>\n\n"
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
        back_to_admin_home_page_button[0],
    ]
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
            text=stringify_order(
                order,
                order_type,
                "@" + tg_user.username if tg_user.username else tg_user.full_name,
            ),
            reply_markup=InlineKeyboardMarkup(actions_keyboard),
        )
        return ConversationHandler.END
