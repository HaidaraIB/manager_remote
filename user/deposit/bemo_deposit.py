from telegram import InlineKeyboardMarkup, Update, Chat
from telegram.ext import ContextTypes, ConversationHandler
from common.common import build_user_keyboard, build_back_button
from common.constants import *
from common.back_to_home_page import back_to_user_home_page_button
from user.deposit.common import send_to_check_bemo_deposit
from models import Checker, DepositOrder, PaymentMethod
import os

DEPOSIT_AMOUNT, BEMO_REF_NUM = range(3, 5)


def find_available_checker(method: str, amount: float):
    checkers = Checker.get_workers(check_what="deposit", method=method)
    for c in checkers:
        if amount <= c.pre_balance:
            return True
    return False


async def bemo_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        back_buttons = [
            build_back_button("back_to_deposit_method"),
            back_to_user_home_page_button[0],
        ]
        if not update.callback_query.data.startswith("back"):
            method_name = update.callback_query.data
            context.user_data["deposit_method"] = method_name
            method = PaymentMethod.get_payment_method(name=method_name)
            if not method.on_off:
                await update.callback_query.answer(
                    "هذه الوسيلة متوقفة مؤقتاً ❗️",
                    show_alert=True,
                )
                return

            await update.callback_query.edit_message_text(
                text=(
                    "أدخل المبلغ بين 50 و 500 ألف\n" "الحد الأدنى للإيداع = 50,000 ل.س"
                ),
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        else:
            await update.callback_query.delete_message()
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text=(
                    "أدخل المبلغ بين 50 و 500 ألف\n" "الحد الأدنى للإيداع = 50,000 ل.س"
                ),
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )

        return DEPOSIT_AMOUNT


async def get_deposit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        back_buttons = [
            build_back_button("back_to_deposit_amount"),
            back_to_user_home_page_button[0],
        ]
        method = context.user_data["deposit_method"]
        text = (
            f"قم بإرسال المبلغ المراد إيداعه إلى:\n\n"
            f"<code>{context.bot_data['data'][f'{method}_number']}</code>\n\n"
            f"ثم أرسل رقم عملية الدفع إلى البوت لنقوم بتوثيقها.\n\n"
        )
        if update.message:
            amount = float(update.message.text)
            back_to_deposit_method_buttons = [
                build_back_button("back_to_deposit_method"),
                back_to_user_home_page_button[0],
            ]
            if amount < 50000:
                await update.message.reply_text(
                    text="الحد الأدنى للإيداع = 50,000 ل.س",
                    reply_markup=InlineKeyboardMarkup(back_to_deposit_method_buttons),
                )
                return

            # checker_available = find_available_checker(method, amount)
            # if not checker_available:
            #     await update.message.reply_text(
            #         text="هذه الخدمة متوقفة حالياً ❗️",
            #         reply_markup=InlineKeyboardMarkup(back_to_deposit_method_buttons),
            #     )
            #     context.bot_data["bemo_deposit_off"] = True
            #     return
            # context.bot_data["bemo_deposit_off"] = False

            context.user_data["deposit_amount"] = amount
            await update.message.reply_photo(
                photo=os.getenv("BEMO_REF_NUMBER_GUIDE_PHOTO_ID"),
                caption=text,
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        else:
            await update.callback_query.edit_message_caption(
                caption=text,
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        return BEMO_REF_NUM


back_to_deposit_amount = bemo_deposit


# Old
async def get_bemo_ref_num(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        d_order = DepositOrder.get_one_order(
            ref_num=update.message.text, method=context.user_data["deposit_method"]
        )
        if d_order and d_order.state == "approved":
            await update.message.reply_text(
                text="رقم عملية مكرر ❗️",
            )
            return
        await send_to_check_bemo_deposit(update=update, context=context)

        await update.message.reply_text(
            text="شكراً لك، تم إرسال طلبك إلى قسم المراجعة، سيصلك رد خلال وقت قصير.",
            reply_markup=build_user_keyboard(),
        )

        return ConversationHandler.END
