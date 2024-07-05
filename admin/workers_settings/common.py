from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from common.back_to_home_page import back_to_admin_home_page_button

from constants import *


def build_workers_keyboard(
    workers: list,
    t: str,
) -> list[list[InlineKeyboardButton]]:
    if len(workers) == 1:
        keyboard = [
            [
                InlineKeyboardButton(
                    text=workers[0]["name"],
                    callback_data=(t + str(workers[0]["id"])),
                )
            ]
        ]
    elif len(workers) % 2 == 0:
        keyboard = [
            [
                InlineKeyboardButton(
                    text=workers[i]["name"],
                    callback_data=(t + str(workers[i]["id"])),
                ),
                InlineKeyboardButton(
                    text=workers[i + 1]["name"],
                    callback_data=(t + str(workers[i + 1]["id"])),
                ),
            ]
            for i in range(0, len(workers), 2)
        ]
    else:
        keyboard = [
            [
                InlineKeyboardButton(
                    text=workers[i]["name"],
                    callback_data=(t + str(workers[i]["id"])),
                ),
                InlineKeyboardButton(
                    text=workers[i + 1]["name"],
                    callback_data=(t + str(workers[i + 1]["id"])),
                ),
            ]
            for i in range(0, len(workers) - 1, 2)
        ]
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=workers[-1]["name"],
                    callback_data=(t + str(workers[-1]["id"])),
                )
            ],
        )
    keyboard.append(
        [
            InlineKeyboardButton(
                text="الرجوع🔙",
                callback_data=(f"back to {t}"),
            )
        ]
    )
    keyboard.append(back_to_admin_home_page_button[0])
    return keyboard


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


def build_positions_keyboard(op: str = "add"):
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
                text="تحقق شراء USDT", callback_data=f"{op}_buyusdt_checker"
            ),
        ],
        *build_positions_keyboard(op),
        (
            [InlineKeyboardButton(text="الرجوع🔙", callback_data="back to worker id")]
            if op == "add"
            else []
        ),
        back_to_admin_home_page_button[0] if op != "add" else [],
    ]
    return InlineKeyboardMarkup(add_worker_keyboard)
