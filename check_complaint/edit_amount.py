from telegram import (
    Update,
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from custom_filters import Complaint, ModAmountUserComplaint
from common.common import build_complaint_keyboard, parent_to_child_models_mapper
from check_complaint.respond_to_user import back_from_respond_to_user_complaint
from check_complaint.check_complaint import make_conv_text
from common.constants import EXT_COMPLAINT_LINE

import models


async def handle_edit_amount_user_complaint(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP, Chat.PRIVATE]:
        data = update.callback_query.data.split("_")
        order_type = data[-2]

        await update.callback_query.answer(
            text="قم بالرد على هذه الرسالة بقيمة المبلغ الجديدة.", show_alert=True
        )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="الرجوع عن تعديل المبلغ🔙",
                    callback_data=f"back_from_mod_amount_to_user_complaint_{order_type}_{data[-1]}",
                )
            )
        )


async def edit_order_amount_user_complaint(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP, Chat.PRIVATE]:

        callback_data = update.message.reply_to_message.reply_markup.inline_keyboard[0][
            0
        ].callback_data.split("_")
        serial = int(callback_data[-1])
        order_type = callback_data[-2]

        op = parent_to_child_models_mapper[order_type].get_one_order(serial=serial)
        complaint = models.Complaint.get_complaint(
            order_serial=serial, order_type=order_type
        )
        
        new_amount = float(update.message.text)
        old_amount = op.amount

        await parent_to_child_models_mapper[order_type].edit_order_amount(
            serial=op.serial,
            new_amount=new_amount,
        )

        if op.worker_id:
            updated_amount = new_amount - old_amount
            if order_type in ["withdraw", "busdt"]:
                await models.PaymentAgent.update_worker_approved_withdraws(
                    worker_id=op.worker_id,
                    method=op.method,
                    amount=updated_amount,
                )
            elif order_type == "deposit":
                await models.DepositAgent.update_worker_approved_deposits(
                    worker_id=op.worker_id,
                    amount=updated_amount,
                )

        conv_text = (
            EXT_COMPLAINT_LINE.format(serial)
            +"تم تعديل المبلغ بنجاح ✅\n"
            +f"المبلغ: <b>{new_amount}</b>\n\n"
        )
        conv_text += make_conv_text(complaint_id=complaint.id)
        await update.message.delete()
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=update.message.reply_to_message.id,
            text=conv_text,
            reply_markup=build_complaint_keyboard(
                data=callback_data,
                send_to_worker=update.effective_chat.type != Chat.PRIVATE,
            ),
        )


back_from_mod_amount_user_complaint = back_from_respond_to_user_complaint


handle_edit_amount_user_complaint_handler = CallbackQueryHandler(
    callback=handle_edit_amount_user_complaint,
    pattern="^mod_amount_user_complaint",
)


edit_order_amount_user_complaint_handler = MessageHandler(
    filters=filters.REPLY
    & Complaint()
    & ModAmountUserComplaint()
    & filters.Regex("^\d+$"),
    callback=edit_order_amount_user_complaint,
)


back_from_mod_amount_user_complaint_handler = CallbackQueryHandler(
    callback=back_from_mod_amount_user_complaint,
    pattern="^back_from_mod_amount_to_user_complaint",
)
