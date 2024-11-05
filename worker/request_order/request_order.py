from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Chat
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from worker.request_order.common import (
    build_payment_agent_keyboard,
    build_checker_keyboard,
    send_requested_order,
    orders_dict,
)
from common.constants import *
from common.common import (
    build_back_button,
    format_amount,
    parent_to_child_models_mapper,
)
from common.back_to_home_page import (
    back_to_worker_home_page_button,
    back_to_worker_home_page_handler,
)
from start import worker_command
import models

REQUEST_WHAT, CHECK_POSITION_REQUEST_ORDER, MAX_AMOUNT = range(3)


async def request_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        deposit_agent = models.DepositAgent.get_workers(
            worker_id=update.effective_user.id,
        )
        deposit_agent_keyboard = []
        for d in deposit_agent:
            if d.is_point:
                deposit_agent_keyboard.append(
                    InlineKeyboardButton(
                        text="تنفيذ إيداع وكلاء",
                        callback_data="request_agents deposit after check",
                    )
                )
            else:
                deposit_agent_keyboard.append(
                    InlineKeyboardButton(
                        text="تنفيذ إيداع لاعبين",
                        callback_data="request_players deposit after check",
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
                    callback_data=f"request_check_{c.check_what}",
                )
            )

        payment_agent = models.PaymentAgent.get_workers(
            worker_id=update.effective_user.id
        )
        payment_agent_keyboard = build_payment_agent_keyboard(payment_agent)

        keyboard = [
            deposit_agent_keyboard,
            checker_keyboard,
            *payment_agent_keyboard,
            back_to_worker_home_page_button[0],
        ]

        if len(keyboard) == 1:
            await update.callback_query.answer(
                "ما من مهام موكلة إليك الآن",
                show_alert=True,
            )
            return ConversationHandler.END

        await update.callback_query.edit_message_text(
            text="اختر نوع الطلب:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

        return REQUEST_WHAT


async def request_what(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        role = update.callback_query.data.replace("request_", "")
        context.user_data["request_order_role"] = role
        message_id, group_id, serial = 0, 0, 0
        if "deposit after check" in role:
            is_point_deposit = False
            if role.startswith("agents"):
                is_point_deposit = True
            dac_order = models.DepositOrder.get_deposit_after_check_order(
                is_point_deposit=is_point_deposit
            )
            if not dac_order:
                await update.callback_query.answer(
                    "ليس هناك طلبات تنفيذ إيداع حالياً.",
                    show_alert=True,
                )
                return
            serial = dac_order.serial
            order_type = "deposit"
            message_id = dac_order.pending_process_message_id
            group_id = dac_order.group_id

        elif role.startswith("check"):
            checkers = models.Checker.get_workers(
                worker_id=update.effective_user.id, check_what=role.split("_")[1]
            )
            keyboard = build_checker_keyboard(checkers)
            keyboard.append(build_back_button("back_to_request_what"))
            keyboard.append(back_to_worker_home_page_button[0])
            await update.callback_query.edit_message_text(
                text="اختر الوظفية",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
            return CHECK_POSITION_REQUEST_ORDER

        else:
            back_buttons = [
                build_back_button("back_to_request_what"),
                back_to_worker_home_page_button[0],
            ]
            await update.callback_query.edit_message_text(
                text="أرسل الحد الأعلى لمبلغ الطلب",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
            return MAX_AMOUNT

        await update.callback_query.edit_message_text(text="الرجاء الانتظار...")
        await send_requested_order(
            serial=serial,
            order_type=order_type,
            message_id=message_id,
            group_id=group_id,
            worker_id=update.effective_user.id,
            checker_id=update.effective_user.id if role.startswith("check") else 0,
            state="checking" if role.startswith("check") else "processing",
        )
        await update.callback_query.delete_message()

        return ConversationHandler.END


back_to_request_what = request_order


async def choose_check_position_request_order(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE:
        role = update.callback_query.data.replace("request_", "")

        check_what = role.split("_")[1]
        method = role.split("_")[2]

        c_order = parent_to_child_models_mapper[check_what].get_check_order(
            method=method,
        )
        if not c_order:
            await update.callback_query.answer(
                f"ليس هناك طلبات تحقق {orders_dict[check_what]} {method} حالياً.",
                show_alert=True,
            )
            return

        await update.callback_query.edit_message_text(text="الرجاء الانتظار...")
        await send_requested_order(
            serial=c_order.serial,
            order_type=check_what,
            message_id=c_order.pending_check_message_id,
            group_id=c_order.group_id,
            worker_id=update.effective_user.id,
            checker_id=update.effective_user.id,
            state="checking",
        )
        await update.callback_query.delete_message()

        return ConversationHandler.END


async def get_max_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        max_amount = float(update.message.text)
        role = context.user_data["request_order_role"]
        w_order = models.WithdrawOrder.get_payment_order(
            method=role,
            max_amount=max_amount,
        )
        if not w_order:
            bu_order = models.BuyUsdtdOrder.get_payment_order(
                method=role,
                max_amount=max_amount,
            )
            if not bu_order:
                back_buttons = [
                    build_back_button("back_to_request_what"),
                    back_to_worker_home_page_button[0],
                ]
                await update.message.reply_text(
                    f"ليس هناك طلبات دفع {role} بمبلغ أصغر أو يساوي {format_amount(max_amount)} حالياً.",
                    reply_markup=InlineKeyboardMarkup(back_buttons),
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

        wait_msg = await update.message.reply_text(text="الرجاء الانتظار...")
        await send_requested_order(
            serial=serial,
            order_type=order_type,
            message_id=message_id,
            group_id=group_id,
            worker_id=update.effective_user.id,
            checker_id=update.effective_user.id if role.startswith("check") else 0,
            state="checking" if role.startswith("check") else "processing",
        )
        await wait_msg.delete()

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
                "^request_.*",
            ),
        ],
        CHECK_POSITION_REQUEST_ORDER: [
            CallbackQueryHandler(
                choose_check_position_request_order,
                "^request_check_.*",
            ),
        ],
        MAX_AMOUNT: [
            MessageHandler(
                filters=filters.Regex("^\d+\.?\d*$"),
                callback=get_max_amount,
            )
        ],
    },
    fallbacks=[
        CallbackQueryHandler(
            back_to_request_what,
            "^back_to_request_what$",
        ),
        back_to_worker_home_page_handler,
        worker_command,
    ],
)
