from telegram import (
    Update,
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from common.common import (
    build_user_keyboard,
    payment_method_pattern,
    build_back_button,
    build_methods_keyboard,
    format_amount,
)

from common.decorators import (
    check_if_user_present_decorator,
    check_user_call_on_or_off_decorator,
    check_user_pending_orders_decorator,
)
from common.force_join import check_if_user_member_decorator
from common.back_to_home_page import (
    back_to_user_home_page_handler,
    back_to_user_home_page_button,
)
from start import start_command
from user.busdt.common import *
from models import PaymentMethod, Wallet
from common.constants import *

(
    USDT_TO_BUY_AMOUNT,
    YES_NO_BUSDT,
    BUSDT_METHOD,
    CASH_CODE,
    BUSDT_CHECK,
) = range(5)


@check_user_pending_orders_decorator
@check_user_call_on_or_off_decorator
@check_if_user_present_decorator
@check_if_user_member_decorator
async def busdt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        await update.callback_query.edit_message_text(
            text=(
                f"<b>1 USDT = {context.bot_data['data']['usdt_to_syp']} SYP</b>\n\n"
                "كم تريد أن تبيع؟ 💵\n\n"
            ),
            reply_markup=InlineKeyboardMarkup(back_to_user_home_page_button),
        )
        return USDT_TO_BUY_AMOUNT


async def usdt_to_buy_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        back_buttons = [
            build_back_button("back_to_usdt_to_buy_amount"),
            back_to_user_home_page_button[0],
        ]
        if update.message:
            amount = float(update.message.text)

            if amount <= 0:
                await update.message.reply_text(
                    text="الرجاء إرسال عدد موجب لا يساوي الصفر",
                    reply_markup=InlineKeyboardMarkup(back_buttons),
                )
                return
            
            wal = Wallet.get_wallets(
                amount=amount, method=USDT
            )
            if not wal:
                await update.message.reply_text(
                    text=(
                        "المبلغ المدخل تجاوز الحد المسموح لحسابات الشركة ❗️\n"
                        "جرب مع قيمة أصغر"
                    )
                )
                return
            
            context.user_data["usdt_to_buy_amount"] = amount
        else:
            amount = context.user_data["usdt_to_buy_amount"]

        keyboard = [
            [
                InlineKeyboardButton(text="موافق 👍", callback_data="yes busdt"),
                InlineKeyboardButton(text="غير موافق 👍", callback_data="no busdt"),
            ],
            *back_buttons,
        ]
        text = (
            f"<b>{amount} USDT = {format_amount(amount * context.bot_data['data']['usdt_to_syp'])} SYP</b>\n\n"
            "هل أنت موافق؟"
        )
        if update.message:
            await update.message.reply_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        else:
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        return YES_NO_BUSDT


back_to_usdt_to_buy_amount = busdt


async def yes_no_busdt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        if update.callback_query.data.startswith("no"):
            await update.callback_query.answer(
                "تم الإلغاء",
                show_alert=True,
            )
            await update.callback_query.edit_message_text(
                text=HOME_PAGE_TEXT,
                reply_markup=build_user_keyboard(),
            )
            return ConversationHandler.END
        else:
            busdt_methods = build_methods_keyboard(busdt=True)
            busdt_methods.append(build_back_button("back_to_yes_no_busdt"))
            busdt_methods.append(back_to_user_home_page_button[0])
            await update.callback_query.edit_message_text(
                text="اختر وسيلة الدفع لاستلام أموالك 💳",
                reply_markup=InlineKeyboardMarkup(busdt_methods),
            )
            return BUSDT_METHOD


back_to_yes_no_busdt = usdt_to_buy_amount


async def busdt_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:

        data = update.callback_query.data
        if not data.startswith("back"):
            method = PaymentMethod.get_payment_method(name=data)

            if not method.on_off:
                await update.callback_query.answer(
                    "هذه الوسيلة متوقفة مؤقتاً ❗️",
                    show_alert=True,
                )
                return
            method = data
            context.user_data["payment_method_busdt"] = method
        else:
            method = context.user_data["payment_method_busdt"]

        back_keyboard = [
            build_back_button("back_to_busdt_method"),
            back_to_user_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text=f"أرسل رقم حساب {method}",
            reply_markup=InlineKeyboardMarkup(back_keyboard),
        )
        return CASH_CODE


back_to_busdt_method = yes_no_busdt


async def get_cash_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:

        back_keyboard = [
            build_back_button("back_to_get_cash_code_busdt"),
            back_to_user_home_page_button[0],
        ]
        if update.message:
            context.user_data["payment_method_number_busdt"] = update.message.text

        wal = Wallet.get_wallets(
            amount=context.user_data["usdt_to_buy_amount"], method=USDT
        )
        await update.message.reply_text(
            text=(
                "أرسل الآن العملات إلى المحفظة:\n\n"
                f"<code>{wal.number}</code>\n\n"
                "ثم أرسل لقطة شاشة لعملية الدفع إلى البوت لنقوم بتوثيقها.\n\n"
                "<b>ملاحظة هامة: الشبكة المستخدمه هي TRC20</b>"
            ),
            reply_markup=InlineKeyboardMarkup(back_keyboard),
        )

        return BUSDT_CHECK


back_to_get_cash_code_busdt = busdt_method


async def busdt_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:

        await send_busdt_order_to_check(update, context)

        await update.message.reply_text(
            text="شكراً لك، تم إرسال طلبك إلى قسم المراجعة، سيصلك رد خلال وقت قصير.",
            reply_markup=build_user_keyboard(),
        )
        return ConversationHandler.END


busdt_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(busdt, "^busdt$")],
    states={
        USDT_TO_BUY_AMOUNT: [
            MessageHandler(
                filters=filters.Regex("^[1-9]+\.?\d*$"), callback=usdt_to_buy_amount
            )
        ],
        YES_NO_BUSDT: [CallbackQueryHandler(yes_no_busdt, "^yes busdt$|^no busdt$")],
        BUSDT_METHOD: [CallbackQueryHandler(busdt_method, payment_method_pattern)],
        CASH_CODE: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=get_cash_code,
            )
        ],
        BUSDT_CHECK: [MessageHandler(filters=filters.PHOTO, callback=busdt_check)],
    },
    fallbacks=[
        CallbackQueryHandler(
            back_to_usdt_to_buy_amount, "^back_to_usdt_to_buy_amount$"
        ),
        CallbackQueryHandler(back_to_yes_no_busdt, "^back_to_yes_no_busdt$"),
        CallbackQueryHandler(back_to_busdt_method, "^back_to_busdt_method$"),
        CallbackQueryHandler(
            back_to_get_cash_code_busdt, "^back_to_get_cash_code_busdt$"
        ),
        back_to_user_home_page_handler,
        start_command,
    ],
    name="busdt_handler",
    persistent=True,
)
