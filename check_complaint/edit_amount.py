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

from custom_filters.Complaint import Complaint
from custom_filters.ModAmountUserComplaint import ModAmountUserComplaint

from DB import DB
import os
from common.common import (
    build_complaint_keyboard,
)

from check_complaint.respond_to_user import back_from_respond_to_user_complaint
from check_complaint.check_complaint import make_complaint_data


async def handle_edit_amount_user_complaint(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP, Chat.PRIVATE]:

        data = update.callback_query.data.split("_")
        await update.callback_query.answer(
            text="قم بالرد على هذه الرسالة بقيمة المبلغ الجديدة.", show_alert=True
        )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="الرجوع عن تعديل المبلغ🔙",
                    callback_data=f"back_from_mod_amount_to_user_complaint_{data[-2]}_{data[-1]}",
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

        op = DB.get_one_order(
            order_type=callback_data[-2], serial=int(callback_data[-1])
        )

        data = await make_complaint_data(context, callback_data)

        new_amount = float(update.message.text)
        old_amount = op["amount"]

        await DB.edit_order_amount(
            order_type=callback_data[-2],
            serial=op["serial"],
            new_amount=new_amount,
        )

        if op["worker_id"]:
            if callback_data[-2] in ["withdraw", "buy usdt"]:
                await DB.update_worker_approved_withdraws(
                    worder_id=op["worker_id"],
                    method=op["method"],
                    amount=-old_amount + new_amount,
                )
            elif callback_data[-2] == "deposit":
                await DB.update_worker_approved_deposits(
                    worder_id=op["worker_id"],
                    amount=-old_amount + new_amount,
                )

        text_list = data["text"].split("\n")
        text_list[4] = f"المبلغ: <b>{new_amount}</b>"
        data["text"] = "\n".join(text_list)

        context.user_data["complaint_data"] = data

        reply_to_text = update.effective_message.reply_to_message.text.split("\n")
        if "تم تعديل المبلغ بنجاح✅" not in reply_to_text:
            reply_to_text.insert(
                1, "\nتم تعديل المبلغ بنجاح✅\n" f"المبلغ: <b>{new_amount}</b>\n"
            )
        else:
            reply_to_text[3] = f"المبلغ: <b>{new_amount}</b>"

        await update.message.delete()

        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=update.message.reply_to_message.id,
            text="\n".join(reply_to_text),
            reply_markup=build_complaint_keyboard(
                data=callback_data,
                from_worker=update.effective_chat.type == Chat.PRIVATE,
                send_to_worker=False,
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
