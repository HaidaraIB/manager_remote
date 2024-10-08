from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
)

from telegram.ext import ContextTypes
import models
from common.back_to_home_page import back_to_user_home_page_button
from common.stringifies import stringify_w_with_us_order

parent_to_child_mapper: dict[str, models.TrustedAgent | models.Partner] = {
    "agent": models.TrustedAgent,
    "partner": models.Partner,
}

syrian_govs_en_ar = {
    "Damascus": "دمشق",
    "Aleppo": "حلب",
    "Rif-Dimashq": "ريف دمشق",
    "Daraa": "درعا",
    "Tartous": "طرطوس",
    "Homs": "حمص",
    "Hama": "حماة",
    "Idlib": "إدلب",
    "Raqqa": "الرقة",
    "Deir-Ezor": "دير الزور",
    "Hasakah": "الحسكة",
    "Suwayda": "السويداء",
    "Latakia": "اللاذقية",
    "Kenitra": "القنيطرة",
}


def govs_pattern(callback_data: str):
    try:
        return callback_data.split("_")[0] in syrian_govs_en_ar
    except:
        return False


def build_govs_keyboard():
    govs = [
        "دمشق / Damascus",
        "حلب / Aleppo",
        "ريف دمشق / Rif-Dimashq",
        "درعا / Daraa",
        "طرطوس / Tartous",
        "حمص / Homs",
        "حماة / Hama",
        "إدلب / Idlib",
        "الرقة / Raqqa",
        "دير الزور / Deir-Ezor",
        "الحسكة / Hasakah",
        "السويداء / Suwayda",
        "اللاذقية / Latakia",
        "القنيطرة / Kenitra",
    ]
    return [
        [
            InlineKeyboardButton(
                text=govs[i],
                callback_data=govs[i].split(" / ")[1] + "_gov",
            ),
            InlineKeyboardButton(
                text=govs[i + 1],
                callback_data=govs[i + 1].split(" / ")[1] + "_gov",
            ),
        ]
        for i in range(0, len(govs), 2)
    ]


work_with_us_keyboard = [
    [
        InlineKeyboardButton(
            text="وكيل",
            callback_data="agent_work_with_us",
        )
    ],
    [
        InlineKeyboardButton(
            text="شريك",
            callback_data="partner_work_with_us",
        )
    ],
    back_to_user_home_page_button[0],
]


WORK_WITH_US_DICT = {
    "partner": {
        "text": (
            "هل لديك خبرات رياضية؟ هل تمتلك قناة تيلجرام؟ أو يوتيوب؟ أو صفحة فيس بوك؟\n"
            "بإمكانك الآن بدء شراكتك معن عبر نظام برومو كود والحصول على نسبة تصل إلى 50% من أرباح الشركة\n\n"
            "لا يوجد متطلبات\n"
            "يمكنك البدء الآن"
        ),
        "button": InlineKeyboardButton(
            text="أريد أن أكون شريك",
            callback_data="wanna_be_partner",
        ),
    },
    "agent": {
        "text": (
            "ابدأ من رأس مال 100000 ل.س فقط\n"
            "وابدأ بجني الأرباح\n"
            "5% لكل عملية إيداع\n"
            "2% لكل عملية سحب\n"
            "25% من خسارة لاعبيك هي ربح لك\n\n"
            "دعم على مدار 24 ساعة\n\n"
            "تسهيلات في عمليات الدفع المسبق\n\n"
            "تسهيلات في حال كنت غير قادر على تنفيذ سحوبات لاعبيك"
        ),
        "button": InlineKeyboardButton(
            text="أريد أن أكون وكيل",
            callback_data="wanna_be_agent",
        ),
    },
}


def build_agent_work_with_us_keyboard(serial: int, role: str):
    keyboard = [
        [
            InlineKeyboardButton(
                text="قبول ✅",
                callback_data=f"accept_{role}_{serial}",
            ),
            InlineKeyboardButton(
                text="رفض ❌",
                callback_data=f"decline_{role}_{serial}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="إشعار باستلام الدفع 🔔",
                callback_data=f"notify_{role}_{serial}",
            ),
        ],
    ]
    return keyboard


async def send_to_group(
    context: ContextTypes.DEFAULT_TYPE,
    serial: int,
    media: list[InputMediaPhoto],
    group_id: int,
):
    role_en_to_ar_dict = {
        "agent": "وكيل",
        "partner": "شريك",
    }
    await context.bot.send_media_group(
        chat_id=group_id,
        media=media,
        caption=(
            f"طلب عمل جديد\n\n"
            + f"النوع: <b>{role_en_to_ar_dict[context.user_data['work_with_us_role']]}</b>\n"
            + stringify_w_with_us_order(
                gov=syrian_govs_en_ar[context.user_data["w_with_us_gov"]],
                neighborhood=context.user_data["w_with_us_neighborhood"],
                email=context.user_data["w_with_us_email"],
                phone=context.user_data["w_with_us_phone"],
                amount=context.user_data["w_with_us_amount"],
                ref_num=context.user_data["w_with_us_ref_num"],
                serial=serial,
            )
        ),
    )

    await context.bot.send_location(
        chat_id=group_id,
        latitude=context.user_data["w_with_us_location"][0],
        longitude=context.user_data["w_with_us_location"][1],
        reply_markup=InlineKeyboardMarkup(
            build_agent_work_with_us_keyboard(
                serial, context.user_data["work_with_us_role"]
            )
        ),
    )
