from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButtonRequestUsers,
    KeyboardButtonRequestChat,
    KeyboardButton,
    ReplyKeyboardRemove,
    ReplyKeyboardMarkup,
)

from telegram.ext import (
    ContextTypes,
    ConversationHandler,
)


from telegram.constants import (
    ChatMemberStatus,
    ChatType,
)

from telegram.error import TimedOut, NetworkError

import os
import uuid
import traceback
import functools
import json
import logging
from DB import DB
from constants import *


def check_if_user_created_account_from_bot_decorator(func):
    @functools.wraps(func)
    async def wrapper(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
    ):
        accounts = DB.get_user_accounts(user_id=update.effective_user.id)
        if not accounts:
            await update.callback_query.answer(
                "قم بإنشاء حساب موثق عن طريق البوت أولاً ❗️",
                show_alert=True,
            )
            return ConversationHandler.END
        return await func(update, context, *args, **kwargs)

    return wrapper


def check_if_user_present_decorator(func):
    @functools.wraps(func)
    async def wrapper(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
    ):
        user = DB.get_user(user_id=update.effective_user.id)
        if not user:
            new_user = update.effective_user
            await DB.add_new_user(
                user_id=new_user.id, username=new_user.username, name=new_user.full_name
            )
        return await func(update, context, *args, **kwargs)

    return wrapper


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


def disable_httpx():
    if int(os.getenv("OWNER_ID")) != 755501092:
        logging.getLogger("httpx").setLevel(logging.WARNING)


op_dict_en_to_ar = {
    "withdraw": "سحب",
    "deposit": "إيداع",
    "buy_usdt": "شراء USDT",
}


def payment_method_pattern(callback_data: str):
    return callback_data in list(map(lambda x: x[0], DB.get_payment_methods()))


def build_back_button(data: str):
    return [InlineKeyboardButton(text="الرجوع🔙", callback_data=data)]


def build_user_keyboard():
    keyboard = [
        [InlineKeyboardButton(text="سحب💳", callback_data="withdraw")],
        [InlineKeyboardButton(text="إيداع📥", callback_data="deposit")],
        [InlineKeyboardButton(text="إنشاء حساب موثق™️", callback_data="create account")],
        [
            InlineKeyboardButton(
                text="إضافة حساب سابق➕", callback_data="add existing account"
            )
        ],
        [InlineKeyboardButton(text="شراء USDT💰", callback_data="buy usdt")],
        [InlineKeyboardButton(text="إنشاء شكوى🗳", callback_data="make complaint")],
        [InlineKeyboardButton(text="وكيل موصى به", url="t.me/Melbet_bo")],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_worker_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(
                text="معالجة طلب🈲", callback_data="worker request order"
            ),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_admin_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(
                text="إعدادات الآدمن⚙️🎛",
                callback_data="admin settings",
            )
        ],
        [
            InlineKeyboardButton(
                text="إعدادات الموظف⚙️🧑🏻‍💻",
                callback_data="worker settings",
            )
        ],
        [
            InlineKeyboardButton(
                text="تغيير غروبات📝",
                callback_data="change groups",
            )
        ],
        [
            InlineKeyboardButton(
                text="إعدادات وسائل الدفع⚙️💳",
                callback_data="wallets settings",
            ),
            InlineKeyboardButton(
                text="سعر صرف USDT🇸🇾➡️💲",
                callback_data="update usdt to syp",
            ),
        ],
        [
            InlineKeyboardButton(
                text="تعديل نسب مكافآت👨🏻‍💻",
                callback_data="update percentages",
            ),
        ],
        [
            InlineKeyboardButton(
                text="تفعيل/إلغاء تفعيل وسيلة دفع🔂",
                callback_data="turn payment method on or off",
            ),
        ],
        [
            InlineKeyboardButton(
                text="تفعيل/إلغاء تفعيل أزرار مستخدم🔂",
                callback_data="turn user calls on or off",
            ),
        ],
        [
            InlineKeyboardButton(
                text="إخفاء/إظهار كيبورد معرفة الآيديات🪄",
                callback_data="hide ids keyboard",
            )
        ],
        [
            InlineKeyboardButton(
                text="رسالة جماعية👥",
                callback_data="broadcast",
            )
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_methods_keyboard(buy_usdt: bool = False):
    methods = DB.get_payment_methods()
    if len(methods) == 1:
        payment_methods = [
            [InlineKeyboardButton(text=methods[0][0], callback_data=methods[0][0])]
        ]
    elif len(methods) % 2 == 0:
        payment_methods = [
            [
                InlineKeyboardButton(text=methods[i][0], callback_data=methods[i][0]),
                InlineKeyboardButton(
                    text=methods[i + 1][0], callback_data=methods[i + 1][0]
                ),
            ]
            for i in range(0, len(methods), 2)
        ]
    else:
        payment_methods = [
            [
                InlineKeyboardButton(text=methods[i][0], callback_data=methods[i][0]),
                InlineKeyboardButton(
                    text=methods[i + 1][0], callback_data=methods[i + 1][0]
                ),
            ]
            for i in range(0, len(methods) - 1, 2)
        ]
        payment_methods.append(
            [InlineKeyboardButton(text=methods[-1][0], callback_data=methods[-1][0])]
        )
    if buy_usdt:
        payment_methods[0].pop(0)
    return payment_methods


def callback_button_uuid_generator():
    return uuid.uuid4().hex


def build_complaint_keyboard(data: list, send_to_worker: bool):
    complaint_keyboard = [
        [
            InlineKeyboardButton(
                text="الرد على المستخدم",
                callback_data=f"respond_to_user_complaint_{data[-2]}_{data[-1]}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="تعديل المبلغ",
                callback_data=f"mod_amount_user_complaint_{data[-2]}_{data[-1]}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="إغلاق الشكوى🔐",
                callback_data=f"close_complaint_{data[-2]}_{data[-1]}",
            ),
        ],
    ]
    if send_to_worker:
        complaint_keyboard[0].append(
            InlineKeyboardButton(
                text="إرسال إلى الموظف المسؤول",
                callback_data=f"send_to_worker_user_complaint_{data[-2]}_{data[-1]}",
            )
        )
    return InlineKeyboardMarkup(complaint_keyboard)


async def add_worker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.chat_member.new_chat_member.status == ChatMemberStatus.MEMBER:
        await DB.add_worker(
            worker_id=update.chat_member.from_user.id,
            name=update.chat_member.from_user.full_name,
            username=(
                update.chat_member.from_user.username
                if update.chat_member.from_user.username
                else ""
            ),
        )
        print("Worker added successfully")
    elif update.chat_member.new_chat_member.status == ChatMemberStatus.LEFT:
        await DB.remove_worker(worker_id=update.chat_member.from_user.id)
        print("Worker removed successfully")


async def invalid_callback_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE:
        await update.callback_query.answer("انتهت صلاحية هذا الزر")
        # try:
        #     await update.callback_query.delete_message()
        # except BadRequest:
        #     pass


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    if isinstance(context.error, (TimedOut, NetworkError)):
        return
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    try:
        error = f"""update = {json.dumps(update_str, indent=2, ensure_ascii=False)} 
        
user_data = {str(context.user_data)}
chat_data = {str(context.chat_data)}

{''.join(traceback.format_exception(None, context.error, context.error.__traceback__))}

{'-'*100}


    """

        with open("errors.txt", "a", encoding="utf-8") as f:
            f.write(error)
    except TypeError:
        error = f"""update = TypeError
        
user_data = {str(context.user_data)}
chat_data = {str(context.chat_data)}

{''.join(traceback.format_exception(None, context.error, context.error.__traceback__))}

{'-'*100}


    """

        with open("errors.txt", "a", encoding="utf-8") as f:
            f.write(error)


def create_folders():
    os.makedirs("data/", exist_ok=True)
    os.makedirs("data_test/", exist_ok=True)


request_buttons = [
    [
        KeyboardButton(
            text="معرفة id مستخدم🆔",
            request_users=KeyboardButtonRequestUsers(request_id=0, user_is_bot=False),
        ),
        KeyboardButton(
            text="معرفة id قناة📢",
            request_chat=KeyboardButtonRequestChat(request_id=1, chat_is_channel=True),
        ),
    ],
    [
        KeyboardButton(
            text="معرفة id مجموعة👥",
            request_chat=KeyboardButtonRequestChat(request_id=2, chat_is_channel=False),
        ),
        KeyboardButton(
            text="معرفة id بوت🤖",
            request_users=KeyboardButtonRequestUsers(request_id=3, user_is_bot=True),
        ),
    ],
]


def build_groups_keyboard(op: str):
    return [
        [
            InlineKeyboardButton(
                text="طلبات انشاء الحسابات",
                callback_data=f"{op} accounts_orders_group",
            )
        ],
        [
            InlineKeyboardButton(
                text="معالجة الإيداع قبل التحقق",
                callback_data=f"{op} deposit_orders_group",
            )
        ],
        [
            InlineKeyboardButton(
                text="معالجة الإيداع بعد التحقق",
                callback_data=f"{op} deposit_after_check_group",
            )
        ],
        [
            InlineKeyboardButton(
                text="هدايا الموظفين",
                callback_data=f"{op} worker_gifts_group",
            )
        ],
        [
            InlineKeyboardButton(
                text="طلبات شراء USDT",
                callback_data=f"{op} buy_usdt_orders_group",
            )
        ],
        [
            InlineKeyboardButton(
                text="معالجة السحب قبل التحقق",
                callback_data=f"{op} withdraw_orders_group",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"سحب {USDT}",
                callback_data=f"{op} {USDT}_group",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"سحب {BEMO}",
                callback_data=f"{op} {BEMO}_group",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"سحب {BARAKAH}",
                callback_data=f"{op} {BARAKAH}_group",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"سحب {SYRCASH}",
                callback_data=f"{op} {SYRCASH}_group",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"سحب {MTNCASH}",
                callback_data=f"{op} {MTNCASH}_group",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"سحب {PAYEER}",
                callback_data=f"{op} {PAYEER}_group",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"سحب {PERFECT_MONEY}",
                callback_data=f"{op} {PERFECT_MONEY}_group",
            )
        ],
        [
            InlineKeyboardButton(
                text="شكاوي العملاء",
                callback_data=f"{op} complaints_group",
            )
        ],
    ]
