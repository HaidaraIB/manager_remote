from telegram import InlineKeyboardButton
from telegram.ext import ContextTypes


def build_turn_user_calls_on_or_off_keyboard(context: ContextTypes.DEFAULT_TYPE):
    on_off_dict = {
        True: "🟢",
        False: "🔴",
    }
    if not context.bot_data.get("user_calls", None):
        context.bot_data["user_calls"] = {
            "withdraw": True,
            "deposit": True,
            "create account": True,
            "delete account": True,
            "busdt": True,
            "make complaint": True,
            "work with us": True,
        }
    user_calls_on_off_dict = context.bot_data["user_calls"]
    keyboard = [
        [
            InlineKeyboardButton(
                text=f"سحب {on_off_dict[user_calls_on_off_dict['withdraw']]}",
                callback_data="on_off withdraw",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"إيداع {on_off_dict[user_calls_on_off_dict['deposit']]}",
                callback_data="on_off deposit",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"إنشاء حساب موثق {on_off_dict[user_calls_on_off_dict['create account']]}",
                callback_data="on_off create account",
            ),
            InlineKeyboardButton(
                text=f"حذف حساب {on_off_dict[user_calls_on_off_dict['delete account']]}",
                callback_data="on_off delete account",
            ),
        ],
        [
            InlineKeyboardButton(
                text=f"شراء USDT {on_off_dict[user_calls_on_off_dict['busdt']]}",
                callback_data="on_off busdt",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"إنشاء شكوى {on_off_dict[user_calls_on_off_dict['make complaint']]}",
                callback_data="on_off make complaint",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"عملك معنا {on_off_dict[user_calls_on_off_dict['work with us']]}",
                callback_data="on_off work with us",
            )
        ],
    ]
    return keyboard
