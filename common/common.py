from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButtonRequestUsers,
    KeyboardButtonRequestChat,
    KeyboardButton,
    ReplyKeyboardRemove,
    ReplyKeyboardMarkup,
    error,
    PhotoSize,
    InputMedia,
    Message,
    User,
)

from telegram.ext import ContextTypes
from telegram.constants import ChatType

import models
from common.constants import *
import asyncio
import os
import uuid
import logging
from datetime import datetime

order_dict_en_to_ar = {
    "withdraw": "سحب",
    "deposit": "إيداع",
    "busdt": "شراء USDT",
}


def calc_period(seconds: int):
    days = int(seconds // (3600 * 24))
    hours = int((seconds % (3600 * 24)) // 3600)
    left_minutes = (seconds % 3600) // 60
    left_seconds = seconds - (days * (3600 * 24)) - (hours * 3600) - (left_minutes * 60)

    days_text = f"{days} يوم " if days else ""
    hours_text = f"{hours} ساعة " if hours else ""
    minutes_text = f"{int(left_minutes)} دقيقة " if left_minutes else ""
    seconds_text = f"{int(left_seconds)} ثانية" if left_seconds else ""

    return days_text + hours_text + minutes_text + seconds_text


async def check_referral(context: ContextTypes.DEFAULT_TYPE, new_user: User):
    if context.args:
        try:
            referrer_id = int(context.args[0])
        except ValueError:
            return
        referrer = models.User.get_user(user_id=referrer_id)
        referral = models.Referral.get_by(referred_user_id=new_user.id)
        if referrer and not referral:
            await models.Referral.add(
                referred_user_id=new_user.id,
                referrer_id=referrer_id,
            )


def make_conv_text(conv: list[models.Conv]):
    conv_text = ""
    for m in conv:
        if m.from_user:
            conv_text += f"المستخدم:\n<b>{m.msg}</b>\n\n"
        else:
            conv_text += f"الدعم:\n<b>{m.msg}</b>\n\n"

    return conv_text


async def ensure_positive_amount(amount: float, update: Update):
    if amount <= 0:
        await update.message.reply_text(
            text="يجب أن يكون المبلغ قيمة موجبة لا تساوي الصفر ❗️"
        )
        return False
    return True


async def send_to_photos_archive(
    context: ContextTypes.DEFAULT_TYPE, photo, serial, order_type
):
    p = (
        await context.bot.send_photo(
            chat_id=int(os.getenv("PHOTOS_ARCHIVE")), photo=photo
        )
    ).photo[-1]
    await models.Photo.add(
        [p],
        order_serial=serial,
        order_type=order_type,
    )


parent_to_child_models_mapper: dict[
    str, models.DepositOrder | models.WithdrawOrder | models.BuyUsdtdOrder
] = {
    "withdraw": models.WithdrawOrder,
    "deposit": models.DepositOrder,
    "busdt": models.BuyUsdtdOrder,
}


def format_amount(amount: float):
    return f"{float(amount):,.2f}".rstrip("0").rstrip(".")


def format_datetime(d: datetime):
    return d.replace(tzinfo=TIMEZONE).strftime(r"%d/%m/%Y  %I:%M %p")


def pretty_time_delta(seconds):
    seconds = int(seconds)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        return "%d days %d hours %d minutes %d seconde" % (
            days,
            hours,
            minutes,
            seconds,
        )
    elif hours > 0:
        return "%d hours %d minutes %d seconds" % (hours, minutes, seconds)
    elif minutes > 0:
        return "%d minutes %d seconds" % (minutes, seconds)
    else:
        return "%d seconds" % (seconds,)


def apply_ex_rate(
    method: str,
    amount: float,
    order_type: str,
    context: ContextTypes.DEFAULT_TYPE,
):
    buy_or_sell_dict = {
        "deposit": "buy_rate",
        "withdraw": "sell_rate",
    }
    try:
        ex_rate = context.bot_data["data"][
            f"{method}_to_syp_{buy_or_sell_dict[order_type]}"
        ]
        if order_type == "deposit":
            amount = amount * 0.97 * ex_rate
        else:
            amount = amount * 0.97 / ex_rate
    except:
        ex_rate = 1
    return amount, ex_rate


def check_hidden_keyboard(context: ContextTypes.DEFAULT_TYPE):
    if (
        not context.user_data.get("request_keyboard_hidden", None)
        or not context.user_data["request_keyboard_hidden"]
    ):
        context.user_data["request_keyboard_hidden"] = False

        reply_markup = ReplyKeyboardMarkup(request_buttons, resize_keyboard=True)
    else:
        reply_markup = ReplyKeyboardRemove()
    return reply_markup


async def send_message_to_user(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
    msg: str,
    keyboard: InlineKeyboardMarkup = None,
):
    try:
        message = await context.bot.send_message(
            chat_id=user_id,
            text=msg,
            reply_markup=keyboard,
        )
        return message
    except error.Forbidden as f:
        if "bot was blocked by the user" in f.message:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=("خطأ ❌\n" "لقد قام هذا المستخدم بحظر البوت"),
            )
        return False


async def send_photo_to_user(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
    msg: str,
    photo: PhotoSize,
    keyboard: InlineKeyboardMarkup = None,
):
    try:
        message = await context.bot.send_photo(
            chat_id=user_id,
            photo=photo,
            caption=msg,
            reply_markup=keyboard,
        )
        return message
    except error.Forbidden as f:
        if "bot was blocked by the user" in f.message:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=("خطأ ❌\n" "لقد قام هذا المستخدم بحظر البوت"),
            )
        return False


async def send_media_to_user(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
    msg: str,
    media: list[InputMedia],
):
    try:
        await context.bot.send_media_group(
            chat_id=user_id,
            media=media,
            caption=msg,
        )
        return True
    except error.Forbidden as f:
        if "bot was blocked by the user" in f.message:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=("خطأ ❌\n" "لقد قام هذا المستخدم بحظر البوت"),
            )
        return False


async def notify_workers(
    context: ContextTypes.DEFAULT_TYPE,
    workers: list[models.DepositAgent | models.PaymentAgent | models.Checker],
    text: str,
):
    ids = set(map(lambda x: x.id, workers))
    for i in ids:
        try:
            await context.bot.send_message(
                chat_id=i,
                text=text,
            )
        except:
            pass
        await asyncio.sleep(1)


def disable_httpx():
    if int(os.getenv("OWNER_ID")) != 755501092:
        logging.getLogger("httpx").setLevel(logging.WARNING)


def payment_method_pattern(callback_data: str):
    return callback_data in PAYMENT_METHODS_LIST or callback_data == "طلبات الوكيل"


def build_back_button(data: str):
    return [InlineKeyboardButton(text="الرجوع🔙", callback_data=data)]


def build_accounts_keyboard(user_id: int):
    accounts = models.Account.get_user_accounts(user_id=user_id)
    accounts_keyboard = [
        InlineKeyboardButton(
            text=a.acc_num,
            callback_data=str(a.acc_num).strip(),
        )
        for a in accounts
    ]
    return accounts_keyboard


def build_confirmation_keyboard(data: str):
    keyboard = [
        InlineKeyboardButton(text="نعم 👍", callback_data=f"yes_{data}"),
        InlineKeyboardButton(text="لا 👎", callback_data=f"no_{data}"),
    ]

    return keyboard


def build_user_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(
                text="سحب 💳",
                callback_data="withdraw_settings",
            )
        ],
        [
            InlineKeyboardButton(
                text="إيداع 📥",
                callback_data="deposit",
            )
        ],
        [
            InlineKeyboardButton(
                text="إدارة حساباتك 🛂",
                callback_data="accounts settings",
            )
        ],
        [
            InlineKeyboardButton(
                text="شراء USDT 💰",
                callback_data="busdt",
            )
        ],
        [
            InlineKeyboardButton(
                text="إنشاء شكوى 🗳",
                callback_data="make complaint",
            )
        ],
        [
            InlineKeyboardButton(
                text="عملك معنا 💼",
                callback_data="work with us",
            )
        ],
        [
            InlineKeyboardButton(
                text="وكلاء موصى بهم 🈂️",
                callback_data="trusted agents",
            )
        ],
        # [
        #     InlineKeyboardButton(
        #         text="دعوة الأصدقاء ✉️",
        #         callback_data="referral",
        #     )
        # ],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_worker_keyboard(deposit_agent: bool = False):
    keyboard = [
        [
            InlineKeyboardButton(
                text="معالجة طلب 🈲", callback_data="worker request order"
            ),
        ],
    ]
    if deposit_agent:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text="💳 إعدادات وسائل الدفع ⚙️",
                    callback_data="wallets settings",
                )
            ]
        )
    return InlineKeyboardMarkup(keyboard)


def build_admin_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(
                text="🎛 إعدادات الآدمن ⚙️",
                callback_data="admin settings",
            ),
            InlineKeyboardButton(
                text="🧑🏻‍💻 إعدادات الموظف ⚙️",
                callback_data="worker settings",
            ),
        ],
        [
            InlineKeyboardButton(
                text="📄 إعدادات الطلب ⚙️",
                callback_data="order settings",
            ),
            InlineKeyboardButton(
                text="إعدادات الوكيل ⚙️",
                callback_data="agent_settings",
            ),
        ],
        [
            InlineKeyboardButton(
                text="تغيير غروبات 📝",
                callback_data="change groups",
            )
        ],
        [
            InlineKeyboardButton(
                text="💳 إعدادات وسائل الدفع ⚙️",
                callback_data="wallets settings",
            ),
            InlineKeyboardButton(
                text="تغيير أسعار صرف 💹",
                callback_data="update exchange rates",
            ),
        ],
        [
            InlineKeyboardButton(
                text="إعدادات المكافآت 👨🏻‍💻",
                callback_data="update percentages",
            ),
            InlineKeyboardButton(
                text="عروض 💥",
                callback_data="offers",
            ),
        ],
        [
            InlineKeyboardButton(
                text="تفعيل/إلغاء تفعيل أزرار مستخدم 🔂",
                callback_data="turn user calls on or off",
            ),
        ],
        [
            InlineKeyboardButton(
                text="إخفاء/إظهار كيبورد معرفة الآيديات 🪄",
                callback_data="hide ids keyboard",
            )
        ],
        [
            InlineKeyboardButton(
                text="إحصائيات 📊",
                callback_data="stats",
            )
        ],
        [
            InlineKeyboardButton(
                text="رسالة جماعية 👥",
                callback_data="broadcast",
            )
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_agent_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(
                text="تسجيل الدخول",
                callback_data="login_agent",
            ),
        ],
        [
            InlineKeyboardButton(
                text="إيداع نقطة",
                callback_data="point_deposit",
            ),
        ],
        [
            InlineKeyboardButton(
                text="إيداع لاعبين",
                callback_data="player_deposit",
            ),
            InlineKeyboardButton(
                text="سحب لاعبين",
                callback_data="player_withdraw",
            ),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_methods_keyboard(busdt: bool = False):
    payment_methods: list[list[InlineKeyboardButton]] = []
    for i in range(0, len(PAYMENT_METHODS_LIST), 2):
        row = []
        row.append(
            InlineKeyboardButton(
                text=PAYMENT_METHODS_LIST[i],
                callback_data=PAYMENT_METHODS_LIST[i],
            )
        )
        if i + 1 < len(PAYMENT_METHODS_LIST):
            row.append(
                InlineKeyboardButton(
                    text=PAYMENT_METHODS_LIST[i + 1],
                    callback_data=PAYMENT_METHODS_LIST[i + 1],
                )
            )
        payment_methods.append(row)
    if busdt:
        payment_methods[0].pop(0)
    return payment_methods


def callback_button_uuid_generator():
    return uuid.uuid4().hex


def build_complaint_keyboard(data: list[str], send_to_worker: bool):
    order_type = data[-2]
    complaint_keyboard = [
        [
            InlineKeyboardButton(
                text="الرد على المستخدم",
                callback_data=f"respond_to_user_complaint_{order_type}_{data[-1]}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="تعديل المبلغ",
                callback_data=f"mod_amount_user_complaint_{order_type}_{data[-1]}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="إغلاق الشكوى 🔐",
                callback_data=f"close_complaint_{order_type}_{data[-1]}",
            ),
        ],
    ]
    if send_to_worker:
        complaint_keyboard[0].append(
            InlineKeyboardButton(
                text="إعادة إلى الموظف",
                callback_data=f"send_to_worker_user_complaint_{order_type}_{data[-1]}",
            )
        )
    return InlineKeyboardMarkup(complaint_keyboard)


async def invalid_callback_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE:
        await update.callback_query.answer("انتهت صلاحية هذا الزر")


def create_folders():
    os.makedirs("data/", exist_ok=True)
    os.makedirs("data_test/", exist_ok=True)


request_buttons = [
    [
        KeyboardButton(
            text="معرفة id مستخدم 🆔",
            request_users=KeyboardButtonRequestUsers(request_id=0, user_is_bot=False),
        ),
        KeyboardButton(
            text="معرفة id قناة 📢",
            request_chat=KeyboardButtonRequestChat(request_id=1, chat_is_channel=True),
        ),
    ],
    [
        KeyboardButton(
            text="معرفة id مجموعة 👥",
            request_chat=KeyboardButtonRequestChat(request_id=2, chat_is_channel=False),
        ),
        KeyboardButton(
            text="معرفة id بوت 🤖",
            request_users=KeyboardButtonRequestUsers(request_id=3, user_is_bot=True),
        ),
    ],
]


def build_method_groups_keyboard(op: str):
    payment_methods: list[list] = []
    for i in range(0, len(PAYMENT_METHODS_LIST), 2):
        row = []
        row.append(
            InlineKeyboardButton(
                text=f"سحب {PAYMENT_METHODS_LIST[i]}",
                callback_data=f"{op} {PAYMENT_METHODS_LIST[i]}_group",
            )
        )
        if i + 1 < len(PAYMENT_METHODS_LIST):
            row.append(
                InlineKeyboardButton(
                    text=f"سحب {PAYMENT_METHODS_LIST[i+1]}",
                    callback_data=f"{op} {PAYMENT_METHODS_LIST[i+1]}_group",
                )
            )
        payment_methods.append(row)
    return payment_methods


def build_groups_keyboard(op: str):
    return [
        [
            InlineKeyboardButton(
                text="غروب الشكاوي",
                callback_data=f"{op} complaints_group",
            ),
            InlineKeyboardButton(
                text="غروب التأخير",
                callback_data=f"{op} latency_group",
            ),
        ],
        [
            InlineKeyboardButton(
                text="هدايا الموظفين",
                callback_data=f"{op} worker_gifts_group",
            )
        ],
        [
            InlineKeyboardButton(
                text="إنشاء الحسابات",
                callback_data=f"{op} accounts_orders_group",
            )
        ],
        [
            InlineKeyboardButton(
                text="غروب أرقام العمليات",
                callback_data=f"{op} ref_numbers_group",
            )
        ],
        [
            InlineKeyboardButton(
                text="تنفيذ إيداع",
                callback_data=f"{op} deposit_after_check_group",
            ),
            InlineKeyboardButton(
                text="تنفيذ إيداع وكلاء",
                callback_data=f"{op} agents_deposit_after_check_group",
            ),
            InlineKeyboardButton(
                text="تحقق إيداع",
                callback_data=f"{op} deposit_orders_group",
            ),
        ],
        [
            InlineKeyboardButton(
                text="تحقق شراء USDT",
                callback_data=f"{op} busdt_orders_group",
            )
        ],
        [
            InlineKeyboardButton(
                text="تحقق سحب",
                callback_data=f"{op} withdraw_orders_group",
            )
        ],
        *build_method_groups_keyboard(op),
        [
            InlineKeyboardButton(
                text="طلبات الانضمام (وكيل)",
                callback_data=f"{op} agent_orders_group",
            ),
            InlineKeyboardButton(
                text="طلبات الانضمام (شريك)",
                callback_data=f"{op} partner_orders_group",
            ),
        ],
    ]


def resolve_message(msg: Message):
    media_dict = {
        "photo": msg.photo[-1] if msg.photo else None,
        "video": msg.video,
        "voice": msg.voice,
        "audio": msg.audio,
    }
    media = None
    media_type = None
    for m_type, m in media_dict.items():
        if m:
            media = m
            media_type = m_type
            break

    return media, media_type


async def send_resolved_message(
    media,
    media_type: str,
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
    chat_id: int,
):
    if media:
        func = getattr(context.bot, f"send_{media_type}")
        await func(
            chat_id=chat_id,
            caption=text,
            **{media_type: media},
        )
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
        )
