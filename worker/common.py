from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from common.common import (
    parent_to_child_models_mapper,
    order_dict_en_to_ar,
    send_message_to_user,
    build_worker_keyboard,
)
from models import TrustedAgent, Checker
from custom_filters import DepositAgent
import os


def build_check_order_buttons(serial: int, order_type: str):
    check_order_buttons = [
        (
            [
                InlineKeyboardButton(
                    text="تعديل المبلغ", callback_data=f"edit_deposit_amount_{serial}"
                ),
            ]
            if order_type == "deposit"
            else []
        ),
        [
            InlineKeyboardButton(
                text="إرسال الطلب ⬅️",
                callback_data=f"send_{order_type}_order_{serial}",
            ),
            InlineKeyboardButton(
                text="رفض الطلب ❌",
                callback_data=f"decline_{order_type}_order_{serial}",
            ),
        ],
    ]
    return InlineKeyboardMarkup(check_order_buttons)


async def check_order(update: Update, order_type: str):
    serial = int(update.callback_query.data.split("_")[-1])
    await update.callback_query.edit_message_reply_markup(
        reply_markup=build_check_order_buttons(
            serial=serial,
            order_type=order_type,
        )
    )


async def decline_order(update: Update, order_type: str):
    serial = int(update.callback_query.data.split("_")[-1])

    await update.callback_query.answer(
        text="قم بالرد على هذه الرسالة بسبب الرفض",
        show_alert=True,
    )
    await update.callback_query.edit_message_reply_markup(
        reply_markup=InlineKeyboardMarkup.from_button(
            InlineKeyboardButton(
                text="الرجوع عن الرفض 🔙",
                callback_data=f"back_from_decline_{order_type}_order_{serial}",
            )
        )
    )


async def decline_order_reason(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    order_type: str,
):
    serial = int(
        update.message.reply_to_message.reply_markup.inline_keyboard[0][
            0
        ].callback_data.split("_")[-1]
    )

    order = parent_to_child_models_mapper[order_type].get_one_order(serial=serial)

    workplace_id = None
    if not getattr(order, "acc_number", None):
        agent = TrustedAgent.get_workers(gov=order.gov, user_id=order.agent_id)
        workplace_id = agent.team_cash_workplace_id

    text = (
        f"تم رفض الطلب ❗️\n\n"
        f"نوع الطلب: <b>{order_dict_en_to_ar[order_type]}</b>\n"
        f"الرقم التسلسلي: <code>{serial}</code>\n\n"
        "سبب الرفض:\n"
        f"<b>{update.message.text_html}</b>"
    )
    await send_message_to_user(
        update=update,
        context=context,
        user_id=order.user_id,
        msg=text,
    )

    text = (
        "تم رفض الطلب ❌\n"
        + update.message.reply_to_message.text_html
        + f"\n\nالسبب:\n<b>{update.message.text_html}</b>"
    )
    if order_type in ["busdt", "deposit"]:
        await context.bot.send_photo(
            chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
            photo=update.message.reply_to_message.photo[-1],
            caption=text,
        )
    else:
        await context.bot.send_message(
            chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
            text=text,
        )

    await context.bot.edit_message_reply_markup(
        chat_id=update.effective_chat.id,
        message_id=update.message.reply_to_message.id,
        reply_markup=InlineKeyboardMarkup.from_button(
            InlineKeyboardButton(
                text="تم رفض الطلب ❌",
                callback_data="❌❌❌❌❌❌❌",
            )
        ),
    )

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="تم رفض الطلب ❌",
        reply_markup=build_worker_keyboard(
            deposit_agent=DepositAgent().filter(update),
        ),
    )
    if not workplace_id:
        await Checker.update_pre_balance(
            check_what="deposit",
            method=order.method,
            worker_id=update.effective_user.id,
            amount=order.amount,
        )
    await parent_to_child_models_mapper[order_type].decline_order(
        reason=update.message.text,
        serial=serial,
    )
