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
    build_back_button,
)
from common.decorators import check_if_user_present_decorator


from common.force_join import check_if_user_member_decorator

from common.back_to_home_page import (
    back_to_user_home_page_button,
    back_to_user_home_page_handler,
)

from start import start_command

from DB import DB

from custom_filters.Account import Account

(FULL_NAME, NATIONAL_NUMBER, DECLINE_REASON) = range(3)


@check_if_user_present_decorator
@check_if_user_member_decorator
async def create_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:

        if not context.bot_data["data"]["user_calls"]["create_account"]:
            await update.callback_query.answer("طلبات انشاء الحسابات متوقفة حالياً ❗️")
            return ConversationHandler.END

        elif DB.check_user_pending_orders(
            order_type="create_account",
            user_id=update.effective_user.id,
        ):
            await update.callback_query.answer(
                "لديك طلب إنشاء حساب قيد التنفيذ بالفعل ❗️"
            )
            return ConversationHandler.END

        await update.callback_query.edit_message_text(
            text="حسناً، قم بإرسال اسمك الثلاثي الآن👤🪪",
            reply_markup=InlineKeyboardMarkup(back_to_user_home_page_button),
        )
        return FULL_NAME


async def full_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        context.user_data["full_name"] = update.message.text
        back_buttons = [
            build_back_button("back_to_full_name"),
            back_to_user_home_page_button[0],
        ]
        await update.message.reply_text(
            text="جيد، الآن الرقم الوطني للهوية 2️⃣",
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return NATIONAL_NUMBER


back_to_full_name = create_account


async def national_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:

        serial = await DB.add_create_account_order(
            user_id=update.effective_user.id,
            full_name=context.user_data["full_name"],
            nat_num=int(update.message.text),
        )

        text = (
            f"الاسم الثلاثي: {context.user_data['full_name']}\n"
            f"الرقم الوطني: {update.message.text}\n\n"
            f"<code>{update.effective_user.id}</code>\n"
            "قم بالرد على هذه الرسالة بمعلومات الحساب."
        )
        await context.bot.send_message(
            chat_id=context.bot_data["data"]["accounts_orders_group"],
            text=text,
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="الرفض❌",
                    callback_data=f"decline_create_account_{update.effective_user.id}_{serial}",
                )
            ),
        )

        await update.message.reply_text(
            text="شكراً لك، سيتم مراجعة الصور المرسلة والرد عليك بأقرب وقت.",
            reply_markup=build_user_keyboard(),
        )

        return ConversationHandler.END


def create_invalid_foramt_string():
    res = (
        "تنسيق خاطئ الرجاء الالتزام بالقالب التالي:\n\n"
        "الاسم الثلاثي\n"
        "رقم الحساب\n"
        "كلمة المرور\n\n"
        "مثال:\n"
        "علي أحمد\n"
        "12345\n"
        "abcd123"
        ""
    )
    return res


async def invalid_account_format(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        if (
            not update.effective_chat.id
            == context.bot_data["data"]["accounts_orders_group"]
            or not update.message
        ):
            return
        await update.message.reply_text(text=create_invalid_foramt_string())


async def reply_to_create_account_order(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [Chat.SUPERGROUP, Chat.GROUP]:

        if (
            update.effective_message.reply_to_message.reply_markup.inline_keyboard[0][
                0
            ].text
            == "تمت الموافقة✅"
        ):
            await update.effective_message.reply_text(
                text="تم إنجاز هذا الطلب بالفعل👍"
            )
            return
        data = update.effective_message.reply_to_message.reply_markup.inline_keyboard[
            0
        ][0].callback_data.split("_")
        user_id = int(data[-2])
        serial = int(data[-1])

        account = update.message.text.split("\n")
        res = await DB.add_account(
            full_name=account[0],
            acc_num=int(account[1]),
            password=account[2],
            user_id=user_id,
            serial=serial,
        )

        if res:
            await update.effective_message.reply_text(
                text="هذا الحساب مسجل لدينا مسبقاً"
            )
            return

        text = (
            "تمت الموافقة على طلبك لإنشاء حساب✅\n\n"
            "معلومات الحساب:\n\n"
            f"الاسم الثلاثي: <b>{account[0]}</b>\n"
            f"رقم الحساب: <code>{account[1]}</code>\n"
            f"كلمة المرور: <code>{account[2]}</code>"
        )
        try:

            await context.bot.send_message(
                chat_id=user_id,
                text=text,
            )
        except Exception as e:
            print(e)
            await update.message.reply_text(text="لقد قام هذا المستخدم بحظر البوت")
            return

        await context.bot.edit_message_reply_markup(
            chat_id=update.effective_chat.id,
            message_id=update.effective_message.reply_to_message.id,
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="تمت الموافقة✅",
                    callback_data="تمت الموافقة✅",
                )
            ),
        )
        await DB.change_order_state(
            order_type="create_account",
            serial=serial,
            state="approved",
        )


async def decline_create_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.SUPERGROUP, Chat.GROUP]:
        user_id = int(update.callback_query.data.split("_")[-2])
        serial = int(update.callback_query.data.split("_")[-1])
        await update.callback_query.answer(
            text=f"قم بالرد على هذه الرسالة بسبب الرفض",
            show_alert=True,
        )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_row(
                build_back_button(f"back_from_decline_create_account_{user_id}_{serial}")
            ),
        )
        return DECLINE_REASON


async def decline_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.SUPERGROUP, Chat.GROUP]:
        data = update.effective_message.reply_to_message.reply_markup.inline_keyboard[
            0
        ][0].callback_data.split("_")
        user_id = int(data[-2])
        serial = int(data[-1])
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="تم رفض طلبك لإنشاء حساب، السبب:\n\n"
                + update.effective_message.text_html,
            )
        except:
            pass

        await context.bot.edit_message_reply_markup(
            chat_id=update.effective_chat.id,
            message_id=update.effective_message.reply_to_message.id,
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="تم الرفض ❌",
                    callback_data="تم الرفض ❌",
                )
            ),
        )

        await DB.change_order_state(
            order_type="create_account",
            state="declined",
            serial=serial,
        )

        return ConversationHandler.END


async def back_from_decline_create_account(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [Chat.SUPERGROUP, Chat.GROUP]:
        user_id = int(update.callback_query.data.split("_")[-2])
        serial = int(update.callback_query.data.split("_")[-1])
        await update.callback_query.answer(
            text=f"قم بالرد على هذه الرسالة بمعلومات الحساب.",
            show_alert=True,
        )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="رفض⛔️",
                    callback_data=f"decline_create_account_{user_id}_{serial}",
                )
            ),
        )
        return ConversationHandler.END


invalid_account_format_handler = MessageHandler(
    filters=filters.REPLY & ~Account(),
    callback=invalid_account_format,
)
reply_to_create_account_order_handler = MessageHandler(
    filters=filters.REPLY & Account(),
    callback=reply_to_create_account_order,
)

decline_create_account_handler = CallbackQueryHandler(
    decline_create_account,
    "^decline_create_account_\d+_\d+$",
)
decline_account_reason_handler = MessageHandler(
    filters=filters.REPLY,
    callback=decline_reason,
)
back_from_decline_create_account_handler = CallbackQueryHandler(
    back_from_decline_create_account,
    "^back_from_decline_create_account_\d+_\d+$",
)

create_account_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(create_account, "^create account$")],
    states={
        FULL_NAME: [
            MessageHandler(filters=filters.TEXT, callback=full_name),
        ],
        NATIONAL_NUMBER: [
            MessageHandler(filters=filters.Regex("^\d+$"), callback=national_number)
        ],
    },
    fallbacks=[
        CallbackQueryHandler(back_to_full_name, "^back_to_full_name$"),
        back_to_user_home_page_handler,
        start_command,
    ],
)
