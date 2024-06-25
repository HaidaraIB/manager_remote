from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Chat,
    KeyboardButtonRequestUsers,
    KeyboardButtonRequestChat,
    KeyboardButton,
    ReplyKeyboardRemove,
    ReplyKeyboardMarkup,
)

from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler,
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
import json
import logging
from DB import DB

from custom_filters.User import User
from custom_filters.Admin import Admin


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

back_button = [
    [
        InlineKeyboardButton(
            text="العودة إلى القائمة الرئيسية🔙",
            callback_data="back to admin home page",
        )
    ],
]


def payment_method_pattern(callback_data: str):
    return callback_data in list(map(lambda x: x[0], DB.get_payment_methods()))


async def check_if_user_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member = await context.bot.get_chat_member(
        chat_id=int(os.getenv("CHANNEL_ID")), user_id=update.effective_user.id
    )
    if chat_member.status == ChatMemberStatus.LEFT:
        text = f"""لبدء استخدام البوت  يجب عليك الانضمام الى قناة البوت أولاً.
        
✅ اشترك أولاً 👇.
🔗 {os.getenv("CHANNEL_LINK")}

ثم اضغط تحقق✅"""
        check_joined_button = [
            [InlineKeyboardButton(text="تحقق✅", callback_data="check joined")]
        ]
        if update.callback_query:
            await update.callback_query.answer(
                text="لا تقلق، حسابك مجمد لا أكثر، أي رصيدك في الحفظ والصون🙃",
                show_alert=True,
            )
            await update.callback_query.edit_message_text(
                text=text, reply_markup=InlineKeyboardMarkup(check_joined_button)
            )
        else:
            await update.message.reply_text(
                text=text, reply_markup=InlineKeyboardMarkup(check_joined_button)
            )
        return False
    return True


def build_user_keyboard():
    keyboard = [
        [InlineKeyboardButton(text="سحب💳", callback_data="withdraw")],
        [InlineKeyboardButton(text="إيداع📥", callback_data="deposit")],
        [InlineKeyboardButton(text="إنشاء حساب موثق™️", callback_data="create account")],
        [InlineKeyboardButton(text="شراء USDT💰", callback_data="buy usdt")],
        [InlineKeyboardButton(text="إنشاء شكوى🗳", callback_data="make complaint")],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_worker_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(text="معالجة طلب🈲", callback_data="request order"),
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


def build_methods_keyboard():
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
    return payment_methods


def callback_button_uuid_generator():
    return uuid.uuid4().hex


def build_complaint_keyboard(data: dict):
    respond_to_user_callback_data = {
        **data,
        "name": "respond to user complaint",
    }
    mod_amount_callback_data = {
        **data,
        "name": "mod amount user complaint",
    }
    close_complaint_callback_data_dict = {
        **data,
        "name": "close complaint",
    }
    if (
        data.get("from_worker", True)
        or data.get("name", False) == "send to worker user complaint"
    ):
        complaint_keyboard = [
            [
                InlineKeyboardButton(
                    text="الرد على المستخدم",
                    callback_data=respond_to_user_callback_data,
                ),
                InlineKeyboardButton(
                    text="تعديل المبلغ",
                    callback_data=mod_amount_callback_data,
                ),
            ],
            [
                InlineKeyboardButton(
                    text="إغلاق الشكوى🔐",
                    callback_data=close_complaint_callback_data_dict,
                ),
            ],
        ]
    else:
        send_to_worker_callback_data_dict = {
            **data,
            "name": "send to worker user complaint",
        }

        complaint_keyboard = [
            [
                InlineKeyboardButton(
                    text="الرد على المستخدم",
                    callback_data=respond_to_user_callback_data,
                ),
                InlineKeyboardButton(
                    text="إرسال إلى الموظف المسؤول",
                    callback_data=send_to_worker_callback_data_dict,
                ),
            ],
            [
                InlineKeyboardButton(
                    text="تعديل المبلغ",
                    callback_data=mod_amount_callback_data,
                )
            ],
            [
                InlineKeyboardButton(
                    text="إغلاق الشكوى🔐",
                    callback_data=close_complaint_callback_data_dict,
                ),
            ],
        ]
    return InlineKeyboardMarkup(complaint_keyboard)


async def back_to_home_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        is_user_member = await check_if_user_member(update=update, context=context)

        if not is_user_member:
            return

        text = "القائمة الرئيسية🔝"
        keyboard = build_user_keyboard()
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
        return ConversationHandler.END


async def back_to_admin_home_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        await update.callback_query.edit_message_text(
            text="القائمة الرئيسية🔝", reply_markup=build_admin_keyboard()
        )
        return ConversationHandler.END


back_to_user_home_page_handler = CallbackQueryHandler(
    back_to_home_page, "^back to user home page$"
)
back_to_admin_home_page_handler = CallbackQueryHandler(
    back_to_admin_home_page, "^back to admin home page$"
)


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


def create_dot_env():
    if os.path.exists(".env"):
        return
    content = f"""
API_ID = '25770272'
API_HASH = 'd122d5cd1975d6e4db7cfed59502f257'

BOT_TOKEN = '6994000356:AAEQlhyQkQCB9jzaqz_84lLIrDE37BhwmcM'

OWNER_ID = '6190159711'

CHANNEL_ID = '-1001553443218'
CHANNEL_LINK = 'https://t.me/melbetsy'

ARCHIVE_CHANNEL = "-1001997728650"

DB_PATH = 'data/database.sqlite3'
"""
    with open(".env", mode="w") as f:
        f.write(content)


def create_folders():
    os.makedirs("data/", exist_ok=True)


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
                text="معالجة الإيداع قبل التحقق",
                callback_data=f"{op} deposit_orders_group",
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
                text="سحب USDT",
                callback_data=f"{op} USDT_group",
            )
        ],
        [
            InlineKeyboardButton(
                text="سحب بيمو",
                callback_data=f"{op} بيمو🇸🇦🇫🇷_group",
            )
        ],
        [
            InlineKeyboardButton(
                text="سحب بركة",
                callback_data=f"{op} بركة🇧🇭_group",
            )
        ],
        [
            InlineKeyboardButton(
                text="سحب سيريتيل كاش",
                callback_data=f"{op} Syriatel Cash🇸🇾_group",
            )
        ],
        [
            InlineKeyboardButton(
                text="سحب mtn كاش",
                callback_data=f"{op} MTN Cash🇸🇾_group",
            )
        ],
        [
            InlineKeyboardButton(
                text="شكاوي العملاء",
                callback_data=f"{op} complaints_group",
            )
        ],
    ]
