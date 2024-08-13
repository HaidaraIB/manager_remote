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
    CANCEL_BUTTON,
    build_payment_agent_keyboard,
    build_checker_keyboard,
    send_requested_order,
    orders_dict,
)
from common.constants import *
from common.common import (
    build_worker_keyboard,
    build_back_button,
    parent_to_child_models_mapper,
)
from start import worker_command
from custom_filters import DepositAgent
import models

REQUEST_WHAT, CHECK_POSITION_REQUEST_ORDER = range(2)


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
        check_whats = set()
        for c in checker:
            if c.check_what in check_whats:
                continue
            check_whats.add(c.check_what)
            checker_keyboard.append(
                InlineKeyboardButton(
                    text=f"تحقق {orders_dict[c.check_what]}",
                    callback_data=f"request check {c.check_what}",
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
            CANCEL_BUTTON,
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
        role = update.callback_query.data.replace("request ", "")
        message_id, group_id, serial = 0, 0, 0
        if role == "deposit after check":
            dac_order = models.DepositOrder.get_deposit_after_check_order()
            if not dac_order:
                await update.callback_query.answer("ليس هناك طلبات تنفيذ إيداع حالياً.")
                return
            serial = dac_order.serial
            order_type = "deposit"
            message_id = dac_order.pending_process_message_id
            group_id = dac_order.group_id

        elif role.startswith("check"):
            checkers = models.Checker.get_workers(
                worker_id=update.effective_user.id, check_what=role.split(" ")[1]
            )
            keyboard = build_checker_keyboard(checkers)
            keyboard.append(build_back_button("back_to_request_what"))
            keyboard.append(CANCEL_BUTTON)
            await update.callback_query.edit_message_text(
                text="اختر الوظفية",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
            return CHECK_POSITION_REQUEST_ORDER

        else:
            w_order = models.WithdrawOrder.get_payment_order(method=role)
            if not w_order:
                bu_order = models.BuyUsdtdOrder.get_payment_order(method=role)
                if not bu_order:
                    await update.callback_query.answer(
                        f"ليس هناك طلبات دفع {role} حالياً."
                    )
                    return
                serial = bu_order.serial
                order_type = "busdt"
                message_id = bu_order.pending_process_message_id
                group_id = bu_order.group_id
            else:
                serial = w_order.serial
                order_type = "withdraw"
                message_id = w_order.pending_process_message_id
                group_id = w_order.group_id

        await update.callback_query.edit_message_text(text="الرجاء الانتظار...")
        await send_requested_order(
            serial=serial,
            message_id=message_id,
            group_id=group_id,
            worker_id=update.effective_user.id,
            role=role,
            order_type=order_type,
        )
        await update.callback_query.delete_message()

        return ConversationHandler.END


back_to_request_what = request_order


async def choose_check_position_request_order(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE:
        role = update.callback_query.data.replace("request ", "")

        check_what = role.split(" ")[1]
        method = role.split(" ")[2]

        c_order = parent_to_child_models_mapper[check_what].get_check_order(
            method=method
        )
        if not c_order:
            await update.callback_query.answer(
                f"ليس هناك طلبات تحقق {orders_dict[check_what]} {method} حالياً."
            )
            return

        await update.callback_query.edit_message_text(text="الرجاء الانتظار...")
        await send_requested_order(
            serial=c_order.serial,
            message_id=c_order.pending_check_message_id,
            group_id=c_order.group_id,
            worker_id=update.effective_user.id,
            role=role,
            order_type=check_what,
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
    entry_points=[
        CallbackQueryHandler(
            request_order,
            "^worker request order$",
        ),
    ],
    states={
        REQUEST_WHAT: [
            CallbackQueryHandler(
                request_what,
                "^request.*",
            ),
        ],
        CHECK_POSITION_REQUEST_ORDER: [
            CallbackQueryHandler(
                choose_check_position_request_order,
                "^request check .*",
            ),
        ],
    },
    fallbacks=[
        CallbackQueryHandler(
            back_to_request_what,
            "^back_to_request_what$",
        ),
        CallbackQueryHandler(
            cancel_request_order,
            "^cancel request order$",
        ),
        worker_command,
    ],
)
