from telegram import (
    InlineKeyboardButton,
)
from models import (
    WithdrawOrder,
    DepositOrder,
    CreateAccountOrder,
    BuyUsdtdOrder,
)
from user.make_complaint.common import state_dict_en_to_ar
order_settings_dict: dict[
    str, dict[str, WithdrawOrder | DepositOrder | BuyUsdtdOrder | CreateAccountOrder]
] = {
    "withdraw": {
        "cls": WithdrawOrder,
        "t": "سحب"
    },
    "deposit": {
        "cls": DepositOrder,
        "t": "إيداع"
    },
    "buy_usdt": {
        "cls": BuyUsdtdOrder,
        "t": "شراء USDT"
    },
}

def stringify_order(order:WithdrawOrder|DepositOrder|BuyUsdtdOrder, order_type:str):
    return (
        f"تفاصيل الطلب:\n\n"
        f"الرقم التسلسلي: {order.serial}\n"
        f"النوع: <b>{order_settings_dict[order_type]['t']}</b>\n"
        f"المبلغ: <code>{order.amount:,.2f}</code>\n"
        f"وسيلة الدفع: <code>{order.method}</code>\n"
        f"الحالة: <b>{state_dict_en_to_ar[order.state]}</b>\n"
        f"رقم الحساب: <code>{order.acc_number if hasattr(order, "acc_number") else 'لا يوجد'}</code>\n"
        f"سبب إعادة/رفض: <b>{order.reason if order.reason else 'لا يوجد'}</b>\n\n"
        f"جاري العمل عليه: <b>{"نعم" if order.working_on_it else "لا"}</b>\n"
        f"تم إغلاق شكوى عنه : <b>{"نعم" if order.complaint_took_care_of else "لا"}</b>\n"
        f"تاريخ الإنشاء:\n<b>{order.order_date}</b>\n"
        f"تاريخ التحقق:\n<b>{order.send_date if order.send_date else "لا يوجد"}</b>\n"
        f"تاريخ الموافقة:\n<b>{order.approve_date if order.approve_date else "لا يوجد"}</b>\n"
        f"تاريخ الرفض:\n<b>{order.decline_date if order.decline_date else "لا يوجد"}</b>\n"
        f"تاريخ الإعادة:\n<b>{order.return_date if order.return_date else "لا يوجد"}</b>\n"
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
                callback_data="buy_usdt_order#settings",
            )
        ],
    ]
    return keyboard
