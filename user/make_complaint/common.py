from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    PhotoSize,
)

from telegram.ext import (
    ContextTypes,
)

from pyrogram.types import Message

from PyroClientSingleton import PyroClientSingleton
from DB import DB
import os

from common.common import (
    build_back_button
)

from common.back_to_home_page import (
    back_to_user_home_page_button
)

state_dict_en_to_ar = {
    "declined": "مرفوض",
    "approved": "تمت الموافقة",
    "returned": "طلب معاد",
    "pending": "بانتظار التحقق",
    "sent": "بانتظار التنفيذ",
}

choose_operations_text = (
    "يمكنك اختيار الرقم التسلسلي للعملية التي تريد الشكوى عنها من الأسفل⬇️\n\n"
    "<b>ملاحظة: الطلبات التي تمت معالجة شكوى عنها سابقاً ليست ضمن القائمة.</b>"
)

complaints_keyboard = [
    [InlineKeyboardButton(text="إيداع📥", callback_data="deposit complaint")],
    [InlineKeyboardButton(text="سحب💳", callback_data="withdraw complaint")],
    [
        InlineKeyboardButton(
            text="شراء USDT💰",
            callback_data="buyusdt complaint",
        )
    ],
    back_to_user_home_page_button[0],
]

async def handle_complaint_about(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    about: str,
):
    operations = DB.get_orders(order_type=about, user_id=update.effective_user.id)

    if not operations:
        return False

    keyboard = build_operations_keyboard(
        serials=[op["serial"] for op in operations if not op["complaint_took_care_of"]]
    )
    keyboard.append(build_back_button(f"back to complaint about"))
    keyboard.append(back_to_user_home_page_button[0])

    context.user_data["operations_keyboard"] = keyboard

    await update.callback_query.edit_message_text(
        text=choose_operations_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return True


def stringify_order(serial: int, order_type: str):
    op = DB.get_one_order(order_type=order_type, serial=serial)
    payment_method_number = bank_account_name = "لا يوجد"
    if order_type != "deposit":
        payment_method_number = (
            op["payment_method_number"] if op["payment_method_number"] else "لا يوجد"
        )
        bank_account_name = (
            op["bank_account_name"] if op["bank_account_name"] else "لا يوجد"
        )

    return (
        f"الرقم التسلسلي: <code>{op['serial']}</code>\n"
        f"المبلغ: <b>{op['amount']}</b>\n"
        f"وسيلة الدفع: <b>{op['method']}</b>\n"
        f"عنوان الدفع: <code>{payment_method_number}</code>\n"
        f"اسم صاحب الحساب البنكي: <code>{bank_account_name}</code>\n"
        f"الحالة: <b>{state_dict_en_to_ar[op['state']]}</b>\n"
        f"سبب إعادة/رفض: <b>{op['reason'] if op['reason'] else 'لا يوجد'}</b>\n\n"
    )


async def get_photos_from_archive(message_ids: list[int]):
    photos: list[PhotoSize] = []
    cpyro = PyroClientSingleton()

    try:
        await cpyro.start()
    except ConnectionError:
        pass

    ms: list[Message] = await cpyro.get_messages(
        chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
        message_ids=message_ids,
    )
    for m in ms:
        if not m.photo:
            continue
        photos.append(
            PhotoSize(
                file_id=m.photo.file_id,
                file_unique_id=m.photo.file_unique_id,
                width=m.photo.width,
                height=m.photo.height,
                file_size=m.photo.file_size,
            )
        )


    return photos


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

    return keyboard

