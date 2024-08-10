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
from worker.request_order.common import (
    build_payment_agent_keyboard,
    send_requested_order,
    orders_dict,
)
from common.common import build_worker_keyboard, parent_to_child_models_mapper
from start import worker_command
from custom_filters import DepositAgent
import models

REQUEST_WHAT = 0


async def request_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:

        deposit_agent = models.DepositAgent.get_workers(
            worker_id=update.effective_user.id,
            deposit=True,
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
            elif c.check_what == "deposit":
                checker_keyboard.append(
                    InlineKeyboardButton(
                        text="تحقق إيداع", callback_data="request check deposit"
                    )
                )
            else:
                checker_keyboard.append(
                    InlineKeyboardButton(
                        text="تحقق شراء USDT", callback_data="request check busdt"
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
            serial = dac_order.serial
            operation = "deposit"
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
                serial = bu_order.serial
                operation = "busdt"
                message_id = bu_order.pending_process_message_id
                group_id = bu_order.group_id
            else:
                serial = w_order.serial
                operation = "withdraw"
                message_id = w_order.pending_process_message_id
                group_id = w_order.group_id

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
