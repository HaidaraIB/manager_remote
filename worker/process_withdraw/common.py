from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from models import WithdrawOrder, Account
from common.common import send_message_to_user
from common.stringifies import stringify_check_withdraw_order
from user.withdraw.common import make_payment_method_info


def build_process_withdraw_keyboard(serial: int):
    keyboard = [
        [
            InlineKeyboardButton(
                text="إعادة الطلب إلى المستخدم 📥",
                callback_data=f"return_withdraw_order_{serial}",
            ),
            InlineKeyboardButton(
                text="إعادة الطلب إلى الموظف📥",
                callback_data=f"return_to_checker_withdraw_order_{serial}",
            ),
        ]
    ]
    return keyboard


async def return_order_to_checker(
    context: ContextTypes.DEFAULT_TYPE,
    w_order: WithdrawOrder,
    reason: str,
):
    account = Account.get_account(acc_num=w_order.acc_number)
    message = await context.bot.send_message(
        chat_id=w_order.checker_id,
        text=stringify_check_withdraw_order(
            w_type="balance",
            acc_number=w_order.acc_number,
            password=account.password if account else None,
            withdraw_code=w_order.withdraw_code,
            method=w_order.method,
            serial=w_order.serial,
            method_info=make_payment_method_info(
                payment_method_number=w_order.payment_method_number,
                bank_account_name=w_order.bank_account_name,
                method=w_order.method,
            ),
        ),
        reply_markup=InlineKeyboardMarkup.from_button(
            InlineKeyboardButton(
                text="التحقق ☑️", callback_data=f"check_withdraw_order_{w_order.serial}"
            )
        ),
    )

    await WithdrawOrder.add_message_ids(
        serial=w_order.serial,
        pending_check_message_id=message.id,
    )
    await context.bot.send_message(
        chat_id=w_order.checker_id,
        text="تمت إعادة الطلب أعلاه من قبل موظف الدفع، السبب:\n" + f"<b>{reason}</b>",
    )
    await WithdrawOrder.return_order_to_checker(
        serial=w_order.serial,
        reason=reason,
    )


async def return_order_to_user(
    update: Update, context: ContextTypes.DEFAULT_TYPE, w_order: WithdrawOrder
):
    withdraw_code = w_order.withdraw_code
    user_id = w_order.user_id

    text = (
        f"تمت إعادة طلب السحب صاحب الكود: <b>{withdraw_code}</b>❗️\n\n"
        "السبب:\n"
        f"<b>{update.message.text_html}</b>\n\n"
        "قم بالضغط على الزر أدناه وإرفاق المطلوب."
    )

    message = await send_message_to_user(
        update=update,
        context=context,
        user_id=user_id,
        msg=text,
        keyboard=InlineKeyboardMarkup.from_button(
            InlineKeyboardButton(
                text="إرفاق المطلوب",
                callback_data=f"handle_return_withdraw_{update.effective_chat.id}_{w_order.serial}",
            )
        ),
    )

    await WithdrawOrder.return_order_to_user(serial=w_order.serial)
    return message
