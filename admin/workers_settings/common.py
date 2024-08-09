from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Chat,
    User,
)

from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler,
    ConversationHandler
)
from common.common import build_back_button, format_amount
from common.back_to_home_page import back_to_admin_home_page_button

from common.constants import *

from custom_filters.Admin import Admin

from models import DepositAgent, PaymentAgent, Checker

(
    CHOOSE_POSITION,
    CHOOSE_WORKER,
) = range(2)

op_dict_en_to_ar = {
    "withdraw": "سحب",
    "deposit": "إيداع",
    "busdt": "شراء USDT",
}


async def worker_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        worker_settings_keyboard = [
            [
                InlineKeyboardButton(text="إضافة موظف➕", callback_data="add worker"),
                InlineKeyboardButton(text="حذف موظف✖️", callback_data="remove worker"),
            ],
            [
                InlineKeyboardButton(
                    text="عرض الموظفين🔍", callback_data="show worker"
                ),
            ],
            [
                InlineKeyboardButton(text="رصيد 💰", callback_data="balance worker"),
            ],
            back_to_admin_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text="هل تريد:",
            reply_markup=InlineKeyboardMarkup(worker_settings_keyboard),
        )
        return ConversationHandler.END


back_to_worker_settings = worker_settings


async def choose_position(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        if update.callback_query.data.startswith("back"):
            op = update.callback_query.data.split("_")[-1]
        else:
            op = update.callback_query.data.split(" ")[0]
            context.user_data["worker_settings_option"] = op
        await update.callback_query.edit_message_text(
            text="اختر الوظيفة:",
            reply_markup=build_positions_keyboard(op=op),
        )
        return CHOOSE_POSITION


back_to_choose_position = choose_position

back_to_worker_settings_handler = CallbackQueryHandler(
    back_to_worker_settings,
    "^back_to_worker_settings$",
)

worker_settings_handler = CallbackQueryHandler(
    worker_settings,
    "^worker settings$",
)


def build_positions_keyboard(op: str):
    if op == "balance":
        keyboard = build_payment_positions_keyboard("balance")
        keyboard.append(build_back_button("back_to_worker_settings"))
        keyboard.append(back_to_admin_home_page_button[0])
        return InlineKeyboardMarkup(keyboard)
    add_worker_keyboard = [
        [
            InlineKeyboardButton(
                text="تنفيذ إيداع",
                callback_data=f"{op}_deposit after check_worker",
            ),
            InlineKeyboardButton(
                text="تحقق إيداع",
                callback_data=f"{op}_deposit_checker",
            ),
        ],
        [
            InlineKeyboardButton(
                text="تحقق سحب", callback_data=f"{op}_withdraw_checker"
            ),
            InlineKeyboardButton(
                text="تحقق شراء USDT", callback_data=f"{op}_busdt_checker"
            ),
        ],
        *build_payment_positions_keyboard(op),
        (
            build_back_button("back_to_worker_id")
            if op == "add"
            else build_back_button("back_to_worker_settings")
        ),
        back_to_admin_home_page_button[0],
    ]
    return InlineKeyboardMarkup(add_worker_keyboard)


def build_payment_positions_keyboard(op: str):
    keyaboard = [
        [
            InlineKeyboardButton(
                text=f"دفع {USDT}", callback_data=f"{op}_{USDT}_worker"
            ),
        ],
        [
            InlineKeyboardButton(
                text=f"دفع {BARAKAH}", callback_data=f"{op}_{BARAKAH}_worker"
            ),
            InlineKeyboardButton(
                text=f"دفع {BEMO}", callback_data=f"{op}_{BEMO}_worker"
            ),
        ],
        [
            InlineKeyboardButton(
                text=f"دفع {SYRCASH}",
                callback_data=f"{op}_{SYRCASH}_worker",
            ),
            InlineKeyboardButton(
                text=f"دفع {MTNCASH}", callback_data=f"{op}_{MTNCASH}_worker"
            ),
        ],
        [
            InlineKeyboardButton(
                text=f"دفع {PAYEER}", callback_data=f"{op}_{PAYEER}_worker"
            ),
            InlineKeyboardButton(
                text=f"دفع {PERFECT_MONEY}",
                callback_data=f"{op}_{PERFECT_MONEY}_worker",
            ),
        ],
    ]
    return keyaboard


def build_workers_keyboard(
    workers: list[DepositAgent | PaymentAgent | Checker],
    t: str,
) -> list[list[InlineKeyboardButton]]:
    if len(workers) == 1:
        keyboard = [
            [
                InlineKeyboardButton(
                    text=workers[0].name,
                    callback_data=(f"{t} " + str(workers[0].id)),
                )
            ]
        ]
    elif len(workers) % 2 == 0:
        keyboard = [
            [
                InlineKeyboardButton(
                    text=workers[i].name,
                    callback_data=(f"{t} " + str(workers[i].id)),
                ),
                InlineKeyboardButton(
                    text=workers[i + 1].name,
                    callback_data=(f"{t} " + str(workers[i + 1].id)),
                ),
            ]
            for i in range(0, len(workers), 2)
        ]
    else:
        keyboard = [
            [
                InlineKeyboardButton(
                    text=workers[i].name,
                    callback_data=(f"{t} " + str(workers[i].id)),
                ),
                InlineKeyboardButton(
                    text=workers[i + 1].name,
                    callback_data=(f"{t} " + str(workers[i + 1].id)),
                ),
            ]
            for i in range(0, len(workers) - 1, 2)
        ]
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=workers[-1].name,
                    callback_data=(f"{t} " + str(workers[-1].id)),
                )
            ],
        )
    keyboard.append(
        [
            InlineKeyboardButton(
                text="الرجوع🔙",
                callback_data=(f"back_to_{t}"),
            )
        ]
    )
    keyboard.append(back_to_admin_home_page_button[0])
    return keyboard


def create_worker_info_text(
    t_worker: User,
    worker: DepositAgent | PaymentAgent | Checker,
    pos: str,
):
    text = (
        f"آيدي الموظف: <code>{t_worker.id}</code>\n"
        f"اسمه: <b>{t_worker.full_name}</b>\n"
        f"اسم المستخدم: {'@' + t_worker.username if t_worker.username else 'لا يوجد'}\n"
    )
    if pos == "deposit after check":
        text += (
            f"الإيداعات حتى الآن: {format_amount(worker.approved_deposits)}\n"
            f"عددها: {worker.approved_deposits_num}\n"
            f"الإيداعات هذا الاسبوع: {format_amount(worker.approved_deposits_week)}\n"
            f"رصيد المكافآت: {format_amount(worker.weekly_rewards_balance)}\n"
        )

    elif pos in ["deposit", "withdraw", "busdt"]:
        text += f"نوع التحقق: {worker.check_what}\n"

    else:
        text += (
            f"الوظيفة: {"سحب " + worker.method}\n"
            f"السحوبات حتى الآن: {format_amount(worker.approved_withdraws)}\n"
            f"عددها: {worker.approved_withdraws_num}\n"
            f"الدفعات المسبقة:\n{format_amount(worker.pre_balance)}\n"
            f"السحوبات هذا الاسبوع: {format_amount(worker.approved_withdraws_day)}\n"
            f"رصيد المكافآت: {format_amount(worker.daily_rewards_balance)}\n"
        )
    return text
