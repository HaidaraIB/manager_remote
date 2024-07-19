from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Chat,
)

from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
)

from PyroClientSingleton import PyroClientSingleton

from common.common import build_worker_keyboard, parent_to_child_models_mapper
from start import worker_command
from custom_filters import DepositAgent
from constants import *
import models

REQUEST_WHAT = 0

orders_dict = {
    "withdraw": "سحب",
    "deposit": "إيداع",
    "buyusdt": "شراء usdt",
}


def build_payment_agent_keyboard(agent: list[models.PaymentAgent]):
    usdt = []
    syr = []
    banks = []
    payeer = []
    for m in agent:
        button = InlineKeyboardButton(
            text=f"دفع {m.method}",
            callback_data=f"request {m.method}",
        )
        if m.method == USDT:
            usdt.append(button)
        elif m.method in [BARAKAH, BEMO]:
            banks.append(button)
        elif m.method in [SYRCASH, MTNCASH]:
            syr.append(button)
        else:
            payeer.append(button)
    return [usdt, syr, banks, payeer]


async def send_requested_order(
    serial: int,
    message_id: int,
    group_id: int,
    worker_id: int,
    order_type: str,
    operation: str,
):
    cpyro = PyroClientSingleton()
    old_message = await cpyro.get_messages(chat_id=group_id, message_ids=message_id)
    message = await cpyro.copy_message(
        chat_id=worker_id,
        from_chat_id=group_id,
        message_id=message_id,
        reply_markup=old_message.reply_markup,
    )
    if order_type.startswith("check"):
        await parent_to_child_models_mapper[operation].add_message_ids(
            serial=serial,
            checking_message_id=message.id,
        )
    else:
        await parent_to_child_models_mapper[operation].add_message_ids(
            serial=serial,
            processing_message_id=message.id,
        )
    await parent_to_child_models_mapper[operation].set_working_on_it(
        serial=serial,
        working_on_it=1,
        worker_id=worker_id,
    )


async def request_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        context.user_data["requested"] = False
        if context.user_data.get("requested", False):
            await update.callback_query.answer("يمكنك معالجة طلب واحد في المرة❗️")
            return ConversationHandler.END

        deposit_agent = models.DepositAgent.get_workers(
            worker_id=update.effective_user.id
        )
        deposit_agent_button = []
        if deposit_agent:
            deposit_agent_button.append(
                InlineKeyboardButton(
                    text="تنفيذ إيداع", callback_data="request deposit after check"
                )
            )

        checker = models.Checker.get_workers(worker_id=update.effective_user.id)
        checker_keyboard = []
        for c in checker:
            if c.check_what == "withdraw":
                checker_keyboard.append(
                    InlineKeyboardButton(
                        text="تحقق سحب", callback_data="request check withdraw"
                    )
                )
            elif c.check_what == "buy_usdt":
                checker_keyboard.append(
                    InlineKeyboardButton(
                        text="تحقق شراء USDT", callback_data="request check buyusdt"
                    )
                )

        payment_agent = models.PaymentAgent.get_workers(
            worker_id=update.effective_user.id
        )
        payment_agent_keyboard = build_payment_agent_keyboard(payment_agent)

        keyboard = [
            deposit_agent_button,
            checker_keyboard,
            *payment_agent_keyboard,
            [
                InlineKeyboardButton(
                    text="إلغاء❌", callback_data="cancel request order"
                )
            ],
        ]

        if len(keyboard) == 1:
            await update.callback_query.answer("ما من مهام موكلة إليك الآن")
            return ConversationHandler.END

        await update.callback_query.edit_message_text(
            text="اختر نوع الطلب:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

        return REQUEST_WHAT


async def request_what(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        order_type = " ".join(update.callback_query.data.split(" ")[1:])
        operation = ""
        message_id, group_id, serial = 0, 0, 0
        if order_type == "deposit after check":
            dac_order = models.DepositOrder.get_deposit_after_check_order()
            if not dac_order:
                await update.callback_query.answer("ليس هناك طلبات تنفيذ إيداع حالياً.")
                return
            operation = "deposit"
            serial = dac_order.serial
            message_id = dac_order.pending_process_message_id
            group_id = dac_order.group_id

        elif order_type.startswith("check"):
            check_what = order_type.split(" ")[1]
            c_order = parent_to_child_models_mapper[check_what].get_check_order()
            if not c_order:
                await update.callback_query.answer(
                    f"ليس هناك طلبات تحقق {orders_dict[check_what]} حالياً."
                )
                return
            serial = c_order.serial
            operation = check_what
            message_id = c_order.pending_check_message_id
            group_id = c_order.group_id

        else:
            w_order = models.WithdrawOrder.get_payment_order(method=order_type)
            if not w_order:
                bu_order = models.BuyUsdtdOrder.get_payment_order(method=order_type)
                if not bu_order:
                    await update.callback_query.answer(
                        f"ليس هناك طلبات دفع {order_type} حالياً."
                    )
                    return
                operation = "buyusdt"
                message_id = bu_order.pending_process_message_id
                group_id = bu_order.group_id
                serial = bu_order.serial
            else:
                operation = "withdraw"
                message_id = w_order.pending_process_message_id
                group_id = w_order.group_id
                serial = w_order.serial

        await update.callback_query.edit_message_text(text="الرجاء الانتظار...")
        await send_requested_order(
            serial=serial,
            message_id=message_id,
            group_id=group_id,
            worker_id=update.effective_user.id,
            order_type=order_type,
            operation=operation,
        )
        await update.callback_query.delete_message()

        context.user_data["requested"] = True
        return ConversationHandler.END


async def cancel_request_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        await update.callback_query.edit_message_text(
            text="تم الإلغاء👍",
            reply_markup=build_worker_keyboard(
                deposit_agent=DepositAgent().filter(update),
            ),
        )
        return ConversationHandler.END


request_order_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(request_order, "^worker request order$")],
    states={
        REQUEST_WHAT: [CallbackQueryHandler(request_what, "^request.*")],
    },
    fallbacks=[
        CallbackQueryHandler(cancel_request_order, "^cancel request order$"),
        worker_command,
    ],
)
