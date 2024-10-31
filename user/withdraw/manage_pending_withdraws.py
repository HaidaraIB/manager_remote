from telegram import Update, Chat, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from common.common import (
    build_back_button,
    build_confirmation_keyboard,
    build_user_keyboard,
    format_amount,
)
from common.back_to_home_page import (
    back_to_user_home_page_button,
    back_to_user_home_page_handler,
)
from common.constants import *
from common.stringifies import user_stringify_order, stringify_process_withdraw_order
from common.functions import send_deposit_without_check
from user.withdraw.withdraw_settings import back_to_withdraw_settings_handler
from PyroClientSingleton import PyroClientSingleton
import models
from start import start_command

SERIAL, OPTION, CONFIRM_CANCEL, AMOUNT, CONFIRM_SPLIT = range(5)


async def manage_pending_withdraws(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        order = models.WithdrawOrder.get_one_order(
            user_id=update.effective_user.id,
            states=["sent", "split"],
        )
        if not order:
            await update.callback_query.answer(
                text="ليس لديك طلبات معلقة ❗️",
                show_alert=True,
            )
            return ConversationHandler.END

        keyboard = [
            [
                InlineKeyboardButton(
                    text=order.serial,
                    callback_data=str(order.serial),
                )
            ],
            build_back_button("back_to_withdraw_settings"),
            back_to_user_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text="اختر رقم الطلب",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return SERIAL


async def choose_serial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        if not update.callback_query.data.startswith("back"):
            serial = int(update.callback_query.data)
            context.user_data["manage_withdraw_serial"] = serial
        else:
            serial = context.user_data["manage_withdraw_serial"]
        keyboard = [
            [
                InlineKeyboardButton(
                    text="إلغاء الطلب ❌",
                    callback_data="cancel_withdraw_order",
                ),
                InlineKeyboardButton(
                    text="إعادة جزء إلى حسابك 📥",
                    callback_data="split_withdraw_order",
                ),
            ],
            build_back_button("back_to_choose_serial"),
            back_to_user_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text=user_stringify_order(serial=serial, order_type="withdraw"),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return OPTION


back_to_choose_serial = manage_pending_withdraws


async def choose_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        if not update.callback_query.data.startswith("back"):
            option = update.callback_query.data
            context.user_data["manage_withdraw_option"] = option
        else:
            option = context.user_data["manage_withdraw_option"]

        back_buttons = [
            build_back_button("back_to_choose_option"),
            back_to_user_home_page_button[0],
        ]
        if option.startswith("cancel"):
            keyboard = [
                build_confirmation_keyboard("cancel_withdraw"),
                *back_buttons,
            ]
            await update.callback_query.edit_message_text(
                text="هل أنت متأكد من إلغاء طلب السحب وإعادة كامل الرصيد إلى حسابك؟",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
            return CONFIRM_CANCEL
        elif option.startswith("split"):
            await update.callback_query.edit_message_text(
                text="أرسل المبلغ الذي تريد إعادته إلى حسابك",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
            return AMOUNT


back_to_choose_option = choose_serial


async def confirm_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        if update.callback_query.data.startswith("yes"):
            order = models.WithdrawOrder.get_one_order(
                serial=context.user_data["manage_withdraw_serial"]
            )
            if order.state not in ["sent", "split"]:
                await update.callback_query.answer(
                    text="هذا الطلب لم يعد معلقاً ❗️",
                    show_alert=True,
                )
                await update.callback_query.edit_message_text(
                    text=HOME_PAGE_TEXT,
                    reply_markup=build_user_keyboard(),
                )
                return ConversationHandler.END
            await models.WithdrawOrder.cancel(serial=order.serial)
            await send_deposit_without_check(
                acc_number=order.acc_number,
                amount=order.amount,
                context=context,
                method=CANCELED_ORDER.format(order.serial),
                user_id=update.effective_user.id,
            )
            await update.callback_query.edit_message_text(
                text="شكراً لك، سيتم إعادة كامل المبلغ إلى حسابك خلال وقت قصير.",
                reply_markup=build_user_keyboard(),
            )
        else:
            await update.callback_query.answer(
                text="تم الإلغاء",
                show_alert=True,
            )
            await update.callback_query.edit_message_text(
                text=HOME_PAGE_TEXT,
                reply_markup=build_user_keyboard(),
            )
        return ConversationHandler.END


async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        if update.message:
            amount = float(update.message.text)
            order = models.WithdrawOrder.get_one_order(
                serial=context.user_data["manage_withdraw_serial"]
            )
            if amount >= order.amount:
                await update.message.reply_text(
                    text="الرجاء إرسال مبلغ أصغر تماماً من مبلغ الطلب"
                )
                return
            context.user_data["split_withdraw_amount"] = amount
        else:
            amount = context.user_data["split_withdraw_amount"]

        keyboard = [
            build_confirmation_keyboard("split_withdraw"),
            build_back_button("back_to_get_amount"),
            back_to_user_home_page_button[0],
        ]
        await update.message.reply_text(
            text=f"هل أنت متأكد من إعادة مبلغ <b>{format_amount(amount)}</b> إلى حسابك وسحب الباقي؟",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return CONFIRM_SPLIT


back_to_get_amount = choose_option


async def confirm_split(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        if update.callback_query.data.startswith("yes"):
            order = models.WithdrawOrder.get_one_order(
                serial=context.user_data["manage_withdraw_serial"]
            )
            if order.state not in ["sent", "split"]:
                await update.callback_query.answer(
                    text="هذا الطلب لم يعد معلقاً ❗️",
                    show_alert=True,
                )
                await update.callback_query.edit_message_text(
                    text=HOME_PAGE_TEXT,
                    reply_markup=build_user_keyboard(),
                )
                return ConversationHandler.END
            await PyroClientSingleton().delete_messages(
                chat_id=order.group_id,
                message_ids=order.pending_process_message_id,
            )
            message = await context.bot.send_message(
                chat_id=order.group_id,
                text=stringify_process_withdraw_order(
                    amount=order.amount - context.user_data["split_withdraw_amount"],
                    serial=order.serial,
                    method=order.method,
                    payment_method_number=order.payment_method_number,
                ),
                reply_markup=InlineKeyboardMarkup.from_button(
                    InlineKeyboardButton(
                        text="قبول الطلب ✅",
                        callback_data=f"verify_withdraw_order_{order.serial}",
                    )
                ),
            )
            await send_deposit_without_check(
                acc_number=order.acc_number,
                amount=context.user_data["split_withdraw_amount"],
                context=context,
                from_withdraw_serial=order.serial,
                method=SPLIT_ORDER.format(order.serial),
                user_id=update.effective_user.id,
            )
            await models.WithdrawOrder.split(
                pending_process_message_id=message.id,
                serial=order.serial,
                amount=order.amount - context.user_data["split_withdraw_amount"],
            )
            await update.callback_query.edit_message_text(
                text="شكراً لك، سيتم إعادة المبلغ المطلوب إلى حسابك، وسحب ما تبقى خلال وقت قصير.",
                reply_markup=build_user_keyboard(),
            )
        else:
            await update.callback_query.answer(
                text="تم الإلغاء",
                show_alert=True,
            )
            await update.callback_query.edit_message_text(
                text=HOME_PAGE_TEXT,
                reply_markup=build_user_keyboard(),
            )
        return ConversationHandler.END


manage_pending_withdraws_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            manage_pending_withdraws,
            "^manage_pending_withdraws$",
        )
    ],
    states={
        SERIAL: [
            CallbackQueryHandler(
                choose_serial,
                "^\d+$",
            ),
        ],
        OPTION: [
            CallbackQueryHandler(
                choose_option,
                "^((split)|(cancel))_withdraw_order$",
            )
        ],
        CONFIRM_CANCEL: [
            CallbackQueryHandler(
                confirm_cancel,
                "^((yes)|(no))_cancel_withdraw$",
            )
        ],
        AMOUNT: [
            MessageHandler(
                filters=filters.Regex("^\d+\.?\d*$"),
                callback=get_amount,
            )
        ],
        CONFIRM_SPLIT: [
            CallbackQueryHandler(
                confirm_split,
                "^((yes)|(no))_split_withdraw$",
            )
        ],
    },
    fallbacks=[
        start_command,
        back_to_user_home_page_handler,
        back_to_withdraw_settings_handler,
        CallbackQueryHandler(back_to_choose_option, "^back_to_choose_option$"),
        CallbackQueryHandler(back_to_choose_serial, "^back_to_choose_serial$"),
        CallbackQueryHandler(back_to_get_amount, "^back_to_get_amount$"),
    ],
    name="manage_pending_withdraws_handler",
    persistent=True,
)
