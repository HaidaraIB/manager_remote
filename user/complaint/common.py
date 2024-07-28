from telegram import (
    InlineKeyboardButton,
)
from common.common import (
    build_back_button,
    parent_to_child_models_mapper,
    format_amount,
)
from common.constants import *
from common.back_to_home_page import back_to_user_home_page_button

NO_OPERATIONS_TEXT = "لم تقم بأي عملية {} بعد ❗️\n" "You didn't make any {} order ❗️"
RETURN_COMPLAINT_TEXT = (
    "<b>طلب معاد راجع محادثة البوت وقم بإرفاق المطلوب.\n"
    "في حال لم تجدها أعد تقديم الطلب من جديد، مع الأخذ بعين الاعتبار سبب الإعادة.</b>\n\n"
    "<b>Returned order, check your chat with the bot and send the attachemts.\n"
    "In case you didn't find any</b>\n\n"
)
NOTIFY_BUTTON_TEXT = "إرسال تنبيه 🔔 - Send notification 🔔"
SP_TEXT = (
    "<b>عملية قيد {}، يمكنك إرسال تذكير بشأنها.</b>\n\n"
    "<b>{} order, you can send a notification about it.</b>\n\n"
)
SEND_REASON_TEXT = (
    "<b>أرسل سبب هذه الشكوى</b>\n\n" "<b>Send the reason of this complaint</b>"
)
THANK_YOU_TEXT = (
    "شكراً لك، تم إرسال الشكوى خاصتك إلى قسم المراجعة بنجاح، سنعمل على إصلاح المشكلة والرد عليك في أقرب وقت ممكن.\n\n"
    "Thank you, we received your request, we'll work on it and respond as soon as possible."
)

state_dict_en_to_ar = {
    "declined": "مرفوض - Declined",
    "approved": "تمت الموافقة - Approved",
    "returned": "طلب معاد - Returned",
    "pending": "بانتظار التحقق - Pending",
    "sent": "بانتظار التنفيذ - Processing",
}


complaints_keyboard = [
    [InlineKeyboardButton(text=DEPOSIT_BUTTON_TEXT, callback_data="deposit complaint")],
    [
        InlineKeyboardButton(
            text=WITHDRAW_BUTTON_TEXT, callback_data="withdraw complaint"
        )
    ],
    [InlineKeyboardButton(text=BUY_USDT_BUTTON_TEXT, callback_data="busdt complaint")],
    back_to_user_home_page_button[0],
]


def stringify_order(serial: int, order_type: str):
    op = parent_to_child_models_mapper[order_type].get_one_order(serial=serial)
    payment_method_number = bank_account_name = NONE_TEXT
    if order_type != "deposit":
        payment_method_number = (
            op.payment_method_number if op.payment_method_number else NONE_TEXT
        )
        bank_account_name = op.bank_account_name if op.bank_account_name else NONE_TEXT

    return (
        f"الرقم التسلسلي: <code>{op.serial}</code>\n"
        f"المبلغ: <b>{format_amount(op.amount)}</b>\n"
        f"وسيلة الدفع: <b>{op.method}</b>\n"
        f"عنوان الدفع: <code>{payment_method_number}</code>\n"
        f"اسم صاحب الحساب البنكي: <code>{bank_account_name}</code>\n"
        f"الحالة: <b>{state_dict_en_to_ar[op.state]}</b>\n"
        f"سبب إعادة/رفض: <b>{op.reason if op.reason else NONE_TEXT}</b>\n\n"
        f"Serial: <code>{op.serial}</code>\n"
        f"Amount: <b>{format_amount(op.amount)}</b>\n"
        f"Payment Method: <b>{op.method}</b>\n"
        f"Payment Info: <code>{payment_method_number}</code>\n"
        f"Bank Account Name: <code>{bank_account_name}</code>\n"
        f"State: <b>{state_dict_en_to_ar[op.state]}</b>\n"
        f"Decline/Return Reason: <b>{op.reason if op.reason else NONE_TEXT}</b>\n\n"
    )


def build_operations_keyboard(serials: list[int]):
    if len(serials) % 3 == 0:
        keyboard = [
            [
                InlineKeyboardButton(
                    text=str(serials[i]), callback_data=f"serial {serials[i]}"
                ),
                InlineKeyboardButton(
                    text=str(serials[i + 1]), callback_data=f"serial {serials[i+1]}"
                ),
                InlineKeyboardButton(
                    text=str(serials[i + 2]), callback_data=f"serial {serials[i+2]}"
                ),
            ]
            for i in range(0, len(serials), 3)
        ]
    elif len(serials) % 3 == 1:
        keyboard = [
            [
                InlineKeyboardButton(
                    text=str(serials[i]), callback_data=f"serial {serials[i]}"
                ),
                InlineKeyboardButton(
                    text=str(serials[i + 1]), callback_data=f"serial {serials[i+1]}"
                ),
                InlineKeyboardButton(
                    text=str(serials[i + 2]), callback_data=f"serial {serials[i+2]}"
                ),
            ]
            for i in range(0, len(serials) - 1, 3)
        ]
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=str(serials[-1]), callback_data=f"serial {serials[-1]}"
                )
            ]
        )
    else:
        keyboard = [
            [
                InlineKeyboardButton(
                    text=str(serials[i]), callback_data=f"serial {serials[i]}"
                ),
                InlineKeyboardButton(
                    text=str(serials[i + 1]), callback_data=f"serial {serials[i+1]}"
                ),
                InlineKeyboardButton(
                    text=str(serials[i + 2]), callback_data=f"serial {serials[i+2]}"
                ),
            ]
            for i in range(0, len(serials) - 2, 3)
        ]
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=str(serials[-2]), callback_data=f"serial {serials[-2]}"
                ),
                InlineKeyboardButton(
                    text=str(serials[-1]), callback_data=f"serial {serials[-1]}"
                ),
            ]
        )
    keyboard.append(build_back_button(f"back_to_complaint_about"))
    keyboard.append(back_to_user_home_page_button[0])
    return keyboard
