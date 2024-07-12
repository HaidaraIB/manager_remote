from telegram import (
    InlineKeyboardButton,
)

from common.back_to_home_page import back_to_user_home_page_button

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


def build_govs_keyboard():
    govs = [
        "دمشق Damascus",
        "حلب Aleppo",
        "ريف دمشق Rif-Dimashq",
        "درعا Daraa",
        "طرطوس Tartous",
        "حمص Homs",
        "حماة Hama",
        "إدلب Idlib",
        "الرقة Raqqa",
        "دير الزور Deir-Ezor",
        "الحسكة Hasakah",
        "السويداء Suwayda",
        "اللاذقية Latakia",
        "القنيطرة Kenitra",
    ]
    return [
        [
            InlineKeyboardButton(
                text=govs[i],
                callback_data=govs[i].split(" ")[1] + "_gov",
            ),
            InlineKeyboardButton(
                text=govs[i + 1],
                callback_data=govs[i + 1].split(" ")[1] + "_gov",
            ),
        ]
        for i in range(0, len(govs), 2)
    ]


def stringify_agent_order(
    ref_num: float,
    gov: str,
    neighborhood: str,
    serial: int,
):
    return (
        "طلب عمل جديد\n\n"
        "النوع: <b>وكيل</b>\n"
        f"المحافظة: <b>{gov}</b>\n"
        f"الحي: <b>{neighborhood}</b>\n"
        f"رقم العملية: <code>{ref_num}</code>\n"
        f"Serial: <code>{serial}</code>"
    )


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
