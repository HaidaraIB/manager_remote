from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Chat,
    User,
)

from telegram.ext import ContextTypes, CallbackQueryHandler, ConversationHandler
from common.common import build_back_button, format_amount, op_dict_en_to_ar
from common.back_to_home_page import back_to_admin_home_page_button

from common.constants import *

from custom_filters.Admin import Admin

from models import DepositAgent, PaymentAgent, Checker

(
    CHOOSE_POSITION,
    CHECK_POSITION_SHOW_REMOVE,
    CHOOSE_WORKER,
) = range(3)


async def worker_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        worker_settings_keyboard = [
            [
                InlineKeyboardButton(text="إضافة موظف➕", callback_data="add_worker"),
                InlineKeyboardButton(text="حذف موظف✖️", callback_data="remove_worker"),
            ],
            [
                InlineKeyboardButton(
                    text="عرض الموظفين🔍", callback_data="show_worker"
                ),
            ],
            [
                InlineKeyboardButton(text="رصيد 💰", callback_data="balance_worker"),
            ],
            back_to_admin_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text="هل تريد:",
            reply_markup=InlineKeyboardMarkup(worker_settings_keyboard),
        )
        return ConversationHandler.END


back_to_choose_option = worker_settings


async def choose_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        if update.callback_query.data.startswith("back"):
            op = update.callback_query.data.split("_")[-1]
        else:
            op = update.callback_query.data.split("_")[0]
            context.user_data["worker_settings_option"] = op
        await update.callback_query.edit_message_text(
            text="اختر الوظيفة:",
            reply_markup=build_positions_keyboard(op=op),
        )
        return CHOOSE_POSITION


back_to_choose_position = choose_option

back_to_choose_option_handler = CallbackQueryHandler(
    back_to_choose_option,
    "^back_to_choose_option$",
)

worker_settings_handler = CallbackQueryHandler(
    worker_settings,
    "^worker settings$",
)


def build_checker_positions_keyboard(check_what: str, op: str):
    pos_method_list_dict = {
        "deposit": CHECK_DEPOSIT_LIST,
        "withdraw": PAYMENT_METHODS_LIST,
        "busdt": PAYMENT_METHODS_LIST,
    }
    usdt = []
    syr = []
    banks = []
    payeer = []
    for m in pos_method_list_dict[check_what]:
        if check_what == "busdt" and m == USDT:
            continue
        button = InlineKeyboardButton(
            text=f"تحقق {m}",
            callback_data=f"{op}_{m}_checker",
        )
        if m == USDT:
            usdt.append(button)
        elif m in [BARAKAH, BEMO]:
            banks.append(button)
        elif m in [SYRCASH, MTNCASH]:
            syr.append(button)
        else:
            payeer.append(button)
    return [usdt, banks, syr, payeer]


def build_positions_keyboard(op: str):
    if op == "balance":
        keyboard = build_payment_positions_keyboard("balance")
        keyboard.append(build_back_button("back_to_choose_option"))
        keyboard.append(back_to_admin_home_page_button[0])
        return InlineKeyboardMarkup(keyboard)
    add_worker_keyboard = [
        [
            InlineKeyboardButton(
                text="تنفيذ إيداع",
                callback_data=f"{op}_deposit after check_worker",
            )
        ],
        [
            InlineKeyboardButton(
                text="تحقق سحب", callback_data=f"{op}_withdraw_checker"
            ),
            InlineKeyboardButton(
                text="تحقق إيداع", callback_data=f"{op}_deposit_checker"
            ),
            InlineKeyboardButton(
                text="تحقق شراء USDT", callback_data=f"{op}_busdt_checker"
            ),
        ],
        *build_payment_positions_keyboard(op),
        (
            build_back_button("back_to_worker_id")
            if op == "add"
            else build_back_button("back_to_choose_option")
        ),
        back_to_admin_home_page_button[0],
    ]
    return InlineKeyboardMarkup(add_worker_keyboard)


def build_payment_positions_keyboard(op: str):
    usdt = []
    syr = []
    banks = []
    payeer = []
    for m in PAYMENT_METHODS_LIST:
        button = InlineKeyboardButton(
            text=f"دفع {m}",
            callback_data=f"{op}_{m}_worker",
        )
        if m == USDT:
            usdt.append(button)
        elif m in [BARAKAH, BEMO]:
            banks.append(button)
        elif m in [SYRCASH, MTNCASH]:
            syr.append(button)
        else:
            payeer.append(button)
    return [usdt, syr, banks, payeer]


def build_workers_keyboard(
    workers: list[DepositAgent | PaymentAgent | Checker],
    t: str,
) -> list[list[InlineKeyboardButton]]:
    keyboard: list[list] = []
    for i in range(0, len(workers), 2):
        row = []
        row.append(
            InlineKeyboardButton(
                text=workers[i].name,
                callback_data=f"{t}_{workers[i].id}",
            )
        )
        if i + 1 < len(workers):
            row.append(
                InlineKeyboardButton(
                    text=workers[i + 1].name,
                    callback_data=f"{t}_{workers[i + 1].id}",
                )
            )
        keyboard.append(row)
    keyboard.append(build_back_button(f"back_to_{t}"))
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
        text += (
            f"نوع التحقق: {op_dict_en_to_ar[worker.check_what]}\n"
            f"وسيلة الدفع: {worker.method}\n"
        )

    else:
        text += (
            f"الوظيفة: {'سحب ' + worker.method}\n"
            f"السحوبات حتى الآن: {format_amount(worker.approved_withdraws)}\n"
            f"عددها: {worker.approved_withdraws_num}\n"
            f"الدفعات المسبقة:\n{format_amount(worker.pre_balance)}\n"
            f"السحوبات هذا الاسبوع: {format_amount(worker.approved_withdraws_day)}\n"
            f"رصيد المكافآت: {format_amount(worker.daily_rewards_balance)}\n"
        )
    return text
