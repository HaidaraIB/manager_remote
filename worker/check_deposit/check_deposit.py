from telegram import (
    Chat,
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)

from DB import DB
import os

from custom_filters import Deposit, Declined, Ref

from common.common import (
    build_worker_keyboard,
)

NEW_DEPOSIT_AMOUNT, REF_NUMBER, DECLINE_REASON = range(3)


def build_approve_deposit_keyboard(order):
    approve_deposit_buttons = [
        [
            InlineKeyboardButton(
                text="تحرير المبلغ📝",
                callback_data=f"edit_deposit_amount_{order['serial']}",
            ),
            InlineKeyboardButton(
                text="إضافة رقم مرجعي0️⃣",
                callback_data=f"add_ref_number_{order['serial']}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="إرسال الطلب⬅️",
                callback_data=f"send_deposit_order_{order['serial']}",
            ),
            InlineKeyboardButton(
                text="رفض الطلب❌",
                callback_data=f"decline_deposit_order_{order['serial']}",
            ),
        ],
    ]
    return approve_deposit_buttons


async def check_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        # if update.effective_user.id in context.bot_data["suspended_workers"]:
        #     await update.callback_query.answer(
        #         "تم إيقافك عن العمل إلى حين معالجة الشكاوى الصادرة باسمك."
        #     )
        #     return

        serial = int(update.callback_query.data.split("_")[2])
        d_order = DB.get_one_order(order_type="deposit", serial=serial)

        approve_deposit_keyboard = build_approve_deposit_keyboard(order=d_order)

        context.user_data[serial] = {
            "add_ref_number": None,
            "edit_amount": None,
            "effective_keyboard": approve_deposit_keyboard,
        }

        await DB.add_checker_id(
            order_type="deposit",
            serial=serial,
            checker_id=update.effective_user.id,
        )

        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(approve_deposit_keyboard),
        )


async def edit_deposit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        serial = int(update.callback_query.data.split("_")[-1])
        await update.callback_query.answer(
            text="قم بالرد على هذه الرسالة بقيمة المبلغ.",
            show_alert=True,
        )

        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="إلغاء تحرير مبلغ❌",
                    callback_data=f"cancel_edit_amount_{serial}",
                )
            )
        )
        return NEW_DEPOSIT_AMOUNT


async def new_deposit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        serial = int(
            update.message.reply_to_message.reply_markup.inline_keyboard[0][
                0
            ].callback_data.split("_")[-1]
        )

        await DB.edit_order_amount(
            serial=serial,
            new_amount=float(update.message.text),
            order_type="deposit",
        )

        new_amount = update.message.text

        user_info = update.message.reply_to_message.caption_html.split("\n")

        user_info[1] = f"المبلغ: <code>{new_amount}</code>"

        context.user_data[serial]["edit_amount"] = new_amount

        approve_deposit_keyboard = build_approve_deposit_keyboard(
            order=DB.get_one_order(order_type="deposit", serial=serial),
        )
        context.user_data[serial]["effective_keyboard"] = approve_deposit_keyboard

        await update.message.reply_text(text="تم تحرير المبلغ بنجاح✅")

        await context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=update.message.reply_to_message.id,
        )

        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=update.message.reply_to_message.photo[-1],
            caption="\n".join(user_info),
            reply_markup=InlineKeyboardMarkup(approve_deposit_keyboard),
        )
        return ConversationHandler.END


async def add_ref_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        serial = update.callback_query.data.split("_")[-1]
        await update.callback_query.answer(
            text="قم بالرد على هذه الرسالة بالرقم المرجعي.",
            show_alert=True,
        )

        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="إلغاء إضافة رقم مرجعي❌",
                    callback_data=f"cancel_add_ref_{serial}",
                )
            )
        )
        return REF_NUMBER


async def get_ref_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        serial = int(
            update.message.reply_to_message.reply_markup.inline_keyboard[0][
                0
            ].callback_data.split("_")[-1]
        )

        await DB.add_deposit_order_ref(serial=serial, ref_number=update.message.text)

        caption = update.message.reply_to_message.caption_html
        user_info = caption.split("\n")

        ref_number = update.message.text
        method = user_info[2].split(": ")[1]

        old_ref_number = DB.get_ref_number(number=ref_number, method=method)

        if old_ref_number:

            await update.message.reply_text(
                text="رقم مرجعي مكرر❗️ (تم التعامل معه من قبل)\nتحقق من الأمر🔍"
            )

        else:
            await DB.add_ref_number(number=ref_number, method=method)

            if "الرقم المرجعي" in caption:
                user_info[4] = f"الرقم المرجعي: <b>{ref_number}</b>"
            else:
                user_info.insert(4, f"الرقم المرجعي: <b>{ref_number}</b>")

            context.user_data[serial]["add_ref_number"] = ref_number

            await update.message.reply_text(text="تمت إضافة الرقم المرجعي بنجاح✅")

        await context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=update.message.reply_to_message.id,
        )

        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=update.message.reply_to_message.photo[-1],
            caption="\n".join(user_info),
            reply_markup=InlineKeyboardMarkup(
                context.user_data[serial]["effective_keyboard"]
            ),
        )
        return ConversationHandler.END


async def send_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        serial = int(update.callback_query.data.split("_")[-1])

        if not context.user_data[serial]["add_ref_number"]:
            await update.callback_query.answer("عليك إضافة رقم مرجعي أولاً❗️")
            return

        if not context.user_data[serial]["edit_amount"]:
            await update.callback_query.answer("عليك تحرير المبلغ أولاً❗️")
            return

        caption = update.callback_query.message.caption_html.split("\n")

        del caption[2]
        del caption[3]
        caption.insert(
            5,
            "\n<b>تنبيه: اضغط على رقم الحساب والمبلغ لنسخها كما هي في الرسالة تفادياً للخطأ.</b>",
        )
        message = await context.bot.send_photo(
            chat_id=context.bot_data["data"]["deposit_after_check_group"],
            photo=update.callback_query.message.photo[-1],
            caption="\n".join(caption),
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="قبول الطلب✅", callback_data=f"verify_deposit_order_{serial}"
                )
            ),
        )

        await DB.change_order_state(
            order_type="deposit",
            serial=serial,
            state="sent",
        )
        await DB.change_order_group_id(
            serial=serial,
            group_id=context.bot_data["data"]["deposit_after_check_group"],
            order_type="deposit",
        )
        await DB.add_message_ids(
            serial=serial,
            pending_process_message_id=message.id,
            order_type="deposit",
        )

        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="تم إرسال الطلب✅",
                    callback_data="تم إرسال الطلب✅",
                )
            )
        )

        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text="تم إرسال الطلب✅",
            reply_markup=build_worker_keyboard(),
        )

        context.user_data["requested"] = False
        del context.user_data[serial]
        await DB.set_working_on_it(
            order_type="deposit",
            working_on_it=0,
            serial=serial,
        )


async def decline_deposit_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        serial = int(update.callback_query.data.split("_")[-1])

        await update.callback_query.answer(
            text="قم بالرد على هذه الرسالة بسبب الرفض", show_alert=True
        )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="الرجوع عن الرفض🔙",
                    callback_data=f"back_from_decline_deposit_order_{serial}",
                )
            )
        )
        return DECLINE_REASON


async def decline_deposit_order_reason(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        data = update.message.reply_to_message.reply_markup.inline_keyboard[0][
            0
        ].callback_data

        await DB.change_order_state(
            order_type="deposit",
            serial=data["serial"],
            state="declined",
        )
        await DB.add_order_reason(
            order_type="deposit",
            serial=data["serial"],
            reason=update.message.text,
        )

        text = (
            f"للأسف، تم إلغاء عملية الإيداع <b>{data['amount']}$</b> التي قمت بها.\n\n"
            "السبب:\n"
            "<b>{update.message.text}</b>\n\n"
            "الرقم التسلسلي للطلب: <code>{data['serial']}</code>\n\n"
        )
        try:
            await context.bot.send_message(
                chat_id=data["user_id"],
                text=text,
            )
        except:
            pass

        caption = update.message.reply_to_message.caption_html.split("\n")
        caption.insert(0, "تم رفض الطلب❌")
        caption = "\n".join(caption) + f"\n\nالسبب:\n<b>{update.message.text_html}</b>"
        message = await context.bot.send_photo(
            chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
            photo=update.message.reply_to_message.photo[-1],
            caption=caption,
        )

        await DB.add_message_ids(
            serial=data["serial"],
            archive_message_ids=str(message.id),
            order_type="deposit",
        )

        await context.bot.edit_message_reply_markup(
            chat_id=update.effective_chat.id,
            message_id=update.message.reply_to_message.id,
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="تم رفض الطلب❌", callback_data="تم رفض الطلب❌"
                )
            ),
        )

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="تم رفض الطلب❌",
            reply_markup=build_worker_keyboard(),
        )

        del context.user_data[data["serial"]]
        context.user_data["requested"] = False
        await DB.set_working_on_it(
            order_type="deposit",
            working_on_it=0,
            serial=data["serial"],
        )
        return ConversationHandler.END


async def cancel_deposit_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        serial = int(update.callback_query.data.split("_")[-1])

        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(
                context.user_data[serial]["effective_keyboard"]
            )
        )
        return ConversationHandler.END


async def back_from_decline_deposit_order(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        serial = int(update.callback_query.data.split("_")[-1])

        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(
                context.user_data[serial]["effective_keyboard"]
            )
        )
        return ConversationHandler.END


check_deposit_handler = CallbackQueryHandler(
    callback=check_deposit,
    pattern="^check_deposit",
)

send_order_handler = CallbackQueryHandler(
    callback=send_order,
    pattern="^send_deposit_order",
)


cancel_deposit_check_handler = CallbackQueryHandler(
    callback=cancel_deposit_check,
    pattern="(^cancel_edit_amount)|(^cancel_add_ref)",
)

edit_deposit_amount_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            callback=edit_deposit_amount,
            pattern="^edit_deposit_amount",
        )
    ],
    states={
        NEW_DEPOSIT_AMOUNT: [
            MessageHandler(
                filters=filters.REPLY & filters.Regex("^\d+$") & Deposit(),
                callback=new_deposit_amount,
            )
        ]
    },
    fallbacks=[cancel_deposit_check_handler],
    name="edit_deposit_amount_handler",
    persistent=True,
)

add_ref_number_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            callback=add_ref_number,
            pattern="^add_ref_number",
        )
    ],
    states={
        REF_NUMBER: [
            MessageHandler(
                filters=filters.REPLY & filters.Regex("^\d+$") & Deposit() & Ref(),
                callback=get_ref_number,
            )
        ]
    },
    fallbacks=[cancel_deposit_check_handler],
    name="add_ref_number_handler",
    persistent=True,
)

decline_deposit_order_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            callback=decline_deposit_order,
            pattern="^decline_deposit_order",
        )
    ],
    states={
        DECLINE_REASON: [
            MessageHandler(
                filters=filters.REPLY & filters.TEXT & Deposit() & Declined(),
                callback=decline_deposit_order_reason,
            )
        ]
    },
    fallbacks=[
        CallbackQueryHandler(
            callback=back_from_decline_deposit_order,
            pattern="^back_from_decline_deposit_order",
        )
    ],
    name="decline_deposit_order_handler",
    persistent=True,
)
