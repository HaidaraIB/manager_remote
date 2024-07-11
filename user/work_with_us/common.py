from telegram import (
    InlineKeyboardButton,
)

from common.back_to_home_page import back_to_user_home_page_button


def stringify_agent_order(
    full_name: str,
    pre_balance: float,
    gov: str,
    withdraw_name: str,
):
    return (
        "طلب عمل جديد\n\n"
        "النوع: <b>وكيل</b>\n"
        f"الاسم الثلاثي: <b>{full_name}</b>\n"
        f"مبلغ الإيداع المسبق: <code>{pre_balance}</code>\n"
        f"المحافظة: <b>{gov}</b>\n"
        f"الاسم للظهور أثناء السحب: <b>{withdraw_name}</b>"
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
