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

from telegram.constants import (
    ParseMode,
)

import asyncio
from DB import DB
import os

from custom_filters import Deposit, Declined, Ref

from common import (
    build_worker_keyboard,
)

NEW_DEPOSIT_AMOUNT, REF_NUMBER, DECLINE_REASON = range(3)


def build_approve_deposit_keyboard(data: dict, amount: float):
    edit_deposit_callback_data = {
        **data,
        "amount": amount,
        "name": "edit deposit amount",
    }
    add_ref_number_callback_data = {
        **data,
        "amount": amount,
        "name": "add reference number deposit",
    }
    send_order_callback_data = {
        **data,
        "amount": amount,
        "name": "send deposit order",
    }

    decline_order_callback_data = {
        **data,
        "amount": amount,
        "name": "decline deposit order",
    }
    approve_deposit_buttons = [
        [
            InlineKeyboardButton(
                text="تحرير المبلغ📝", callback_data=edit_deposit_callback_data
            ),
            InlineKeyboardButton(
                text="إضافة رقم مرجعي0️⃣",
                callback_data=add_ref_number_callback_data,
            ),
        ],
        [
            InlineKeyboardButton(
                text="إرسال الطلب⬅️", callback_data=send_order_callback_data
            ),
            InlineKeyboardButton(
                text="رفض الطلب❌", callback_data=decline_order_callback_data
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

        data = update.callback_query.data

        callback_data_dict = {
            **data,
            "worker_id": update.effective_user.id,
        }

        approve_deposit_keyboard = build_approve_deposit_keyboard(
            data=callback_data_dict,
            amount=data["amount"],
        )

        context.user_data[data["serial"]] = {
            "add_ref_number": None,
            "edit_amount": None,
            "effective_keyboard": approve_deposit_keyboard,
        }

        await DB.add_checker_id(
            order_type="deposit",
            serial=data["serial"],
            checker_id=update.effective_user.id,
        )

        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(approve_deposit_keyboard),
        )


async def edit_deposit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        data = update.callback_query.data

        cancel_button_callback_data = {
            **data,
            "name": "cancel edit amount",
        }
        cancel_button = [
            [
                InlineKeyboardButton(
                    text="إلغاء تحرير مبلغ❌",
                    callback_data=cancel_button_callback_data,
                )
            ],
        ]

        await update.callback_query.answer(
            text="قم بالرد على هذه الرسالة بقيمة المبلغ.", show_alert=True
        )

        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(cancel_button)
        )
        return NEW_DEPOSIT_AMOUNT


async def new_deposit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        data = update.message.reply_to_message.reply_markup.inline_keyboard[0][
            0
        ].callback_data

        await DB.edit_order_amount(
            serial=data["serial"],
            new_amount=float(update.message.text),
            order_type="deposit",
        )

        new_amount = update.message.text

        user_info = update.message.reply_to_message.caption_html.split("\n")

        user_info[1] = f"المبلغ: <code>{new_amount}</code>"

        context.user_data[data["serial"]]["edit_amount"] = new_amount

        approve_deposit_keyboard = build_approve_deposit_keyboard(
            data=data, amount=new_amount
        )
        context.user_data[data["serial"]][
            "effective_keyboard"
        ] = approve_deposit_keyboard

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

        data = update.callback_query.data

        cancel_button_callback_data = {
            **data,
            "name": "cancel add ref",
        }
        cancel_button = [
            [
                InlineKeyboardButton(
                    text="إلغاء إضافة رقم مرجعي❌",
                    callback_data=cancel_button_callback_data,
                )
            ],
        ]

        await update.callback_query.answer(
            text="قم بالرد على هذه الرسالة بالرقم المرجعي.",
            show_alert=True,
        )

        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(cancel_button)
        )
        return REF_NUMBER


async def get_ref_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        data = update.message.reply_to_message.reply_markup.inline_keyboard[0][
            0
        ].callback_data

        await DB.add_deposit_order_ref(
            serial=data["serial"], ref_number=update.message.text
        )

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

            context.user_data[data["serial"]]["add_ref_number"] = ref_number

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
                context.user_data[data["serial"]]["effective_keyboard"]
            ),
        )
        return ConversationHandler.END


async def send_order_after(
    after: int,
    context: ContextTypes.DEFAULT_TYPE,
    update: Update,
    caption: list,
    verify_button: list[list[InlineKeyboardButton]],
    data: dict,
):
    await asyncio.sleep(after)
    message = await context.bot.send_photo(
        chat_id=context.bot_data["data"]["deposit_after_check_group"],
        photo=update.callback_query.message.photo[-1],
        caption="\n".join(caption),
        reply_markup=InlineKeyboardMarkup(verify_button),
    )

    await DB.change_order_state(
        order_type="deposit",
        serial=data["serial"],
        state="sent",
    )
    await DB.change_order_group_id(
        serial=data["serial"],
        group_id=context.bot_data["data"]["deposit_after_check_group"],
        order_type="deposit",
    )
    await DB.add_message_ids(
        serial=data["serial"],
        pending_process_message_id=message.id,
        order_type="deposit",
    )


async def send_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        data = update.callback_query.data

        if not context.user_data[data["serial"]]["add_ref_number"]:
            await update.callback_query.answer("عليك إضافة رقم مرجعي أولاً❗️")
            return

        if not context.user_data[data["serial"]]["edit_amount"]:
            await update.callback_query.answer("عليك تحرير المبلغ أولاً❗️")
            return

        verify_button_callback_data = {
            **data,
            "name": "verify deposit order",
        }
        verify_button = [
            [
                InlineKeyboardButton(
                    text="قبول الطلب✅", callback_data=verify_button_callback_data
                )
            ]
        ]

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
            reply_markup=InlineKeyboardMarkup(verify_button),
        )

        await DB.change_order_state(
            order_type="deposit",
            serial=data["serial"],
            state="sent",
        )
        await DB.change_order_group_id(
            serial=data["serial"],
            group_id=context.bot_data["data"]["deposit_after_check_group"],
            order_type="deposit",
        )
        await DB.add_message_ids(
            serial=data["serial"],
            pending_process_message_id=message.id,
            order_type="deposit",
        )

        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="تم إرسال الطلب✅",
                            callback_data="تم إرسال الطلب✅",
                        )
                    ]
                ]
            )
        )

        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text="تم إرسال الطلب✅",
            reply_markup=build_worker_keyboard(),
        )

        context.user_data["requested"] = False
        del context.user_data[data["serial"]]
        await DB.set_working_on_it(
            order_type="deposit",
            working_on_it=0,
            serial=data["serial"],
        )


async def decline_deposit_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        data = update.callback_query.data

        back_button_callback_data = {
            **data,
            "name": "back from decline deposit order",
        }
        decline_deposit_button = [
            [
                InlineKeyboardButton(
                    text="الرجوع عن الرفض🔙",
                    callback_data=back_button_callback_data,
                )
            ],
        ]

        await update.callback_query.answer(
            text="قم بالرد على هذه الرسالة بسبب الرفض", show_alert=True
        )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(decline_deposit_button)
        )
        return DECLINE_REASON


async def decline_deposit_after(
    after: int,
    context: ContextTypes.DEFAULT_TYPE,
    update: Update,
    caption: str,
    data: dict,
):
    await asyncio.sleep(after)
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

        text = f"""للأسف، تم إلغاء عملية الإيداع <b>{data['amount']}$</b> التي قمت بها.

السبب:
<b>{update.message.text}</b>

الرقم التسلسلي للطلب: <code>{data['serial']}</code>

"""
        try:
            await context.bot.send_message(
                chat_id=data["user_id"], text=text,
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
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(text="تم رفض الطلب❌", callback_data="تم رفض الطلب❌"),
                ]
            ])
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

        data = update.callback_query.data

        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(
                context.user_data[data["serial"]]["effective_keyboard"]
            )
        )
        return ConversationHandler.END


async def back_from_decline_deposit_order(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        data = update.callback_query.data

        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(
                context.user_data[data["serial"]]["effective_keyboard"]
            )
        )
        return ConversationHandler.END


check_deposit_handler = CallbackQueryHandler(
    callback=check_deposit,
    pattern=lambda d: isinstance(d, dict) and d.get("name", False) == "check deposit",
)

send_order_handler = CallbackQueryHandler(
    callback=send_order,
    pattern=lambda d: isinstance(d, dict)
    and d.get("name", False) == "send deposit order",
)


cancel_deposit_check_handler = CallbackQueryHandler(
    callback=cancel_deposit_check,
    pattern=lambda d: isinstance(d, dict)
    and d.get("name", False) in ["cancel edit amount", "cancel add ref"],
)

edit_deposit_amount_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            callback=edit_deposit_amount,
            pattern=lambda d: isinstance(d, dict)
            and d.get("name", False) == "edit deposit amount",
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
            pattern=lambda d: isinstance(d, dict)
            and d.get("name", False) == "add reference number deposit",
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
            pattern=lambda d: isinstance(d, dict)
            and d.get("name", False) == "decline deposit order",
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
            pattern=lambda d: isinstance(d, dict)
            and d.get("name", False) == "back from decline deposit order",
        )
    ],
    name="decline_deposit_order_handler",
    persistent=True,
)
