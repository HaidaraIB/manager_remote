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
from common.force_join import check_if_user_member_decorator

from DB import DB

from custom_filters.Account import Account

FULL_NAME, NATIONAL_NUMBER = range(2)
DECLINE_REASON = 18


@check_if_user_member_decorator
async def create_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:

        if not context.bot_data["data"]["user_calls"]["create_account"]:
            await update.callback_query.answer("طلبات انشاء الحسابات متوقفة حالياً❗️")
            return ConversationHandler.END

        user = DB.get_user(user_id=update.effective_user.id)
        if not user:
            new_user = update.effective_user
            await DB.add_new_user(
                user_id=new_user.id, username=new_user.username, name=new_user.full_name
            )

        text = "حسناً، قم بإرسال اسمك الثلاثي الآن👤🪪"
        cancel_button = [
            [
                InlineKeyboardButton(
                    text="إلغاء❌", callback_data="cancel create account"
                )
            ],
        ]
        await update.callback_query.edit_message_text(
            text=text, reply_markup=InlineKeyboardMarkup(cancel_button)
        )
        return FULL_NAME


async def full_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        context.user_data["full_name"] = update.message.text
        await update.message.reply_text(text="جيد، الآن الرقم الوطني للهوية 2️⃣")
        return NATIONAL_NUMBER


async def national_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:

        text = (
            f"الاسم الثلاثي: {context.user_data["full_name"]}\n"
            f"الرقم الوطني: {update.message.text}\n\n"
            f"<code>{update.effective_user.id}</code>\nقم بالرد على هذه الرسالة بصورة الحساب."
        )
        await context.bot.send_message(
            chat_id=context.bot_data["data"]["accounts_orders_group"],
            text=text,
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="الرفض❌",
                    callback_data=f"decline create account {update.effective_user.id}",
                )
            ),
        )

        text = "شكراً لك، سيتم مراجعة الصور المرسلة والرد عليك بأقرب وقت."
        await update.message.reply_text(
            text=text,
            reply_markup=build_user_keyboard(),
        )

        return ConversationHandler.END


async def cancel_create_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        text = f"تم الإلغاء👍\n\n" "قم بإرسال اسمك الثلاثي الآن 👤🪪"

        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=build_user_keyboard(),
        )
        return ConversationHandler.END


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

        user_id = int(update.effective_message.reply_to_message.text.split("\n")[3])
        try:
            text = "تمت الموافقة على طلبك لإنشاء حساب✅"

            try:
                await context.bot.send_photo(
                    chat_id=user_id,
                    caption=text,
                    photo=update.effective_message.photo[-1],
                )
            except:
                pass

            await context.bot.edit_message_reply_markup(
                chat_id=update.effective_chat.id,
                reply_markup=InlineKeyboardMarkup.from_button(
                    InlineKeyboardButton(
                        text="تمت الموافقة✅", callback_data="تمت الموافقة✅"
                    )
                ),
                message_id=update.effective_message.reply_to_message.id,
            )
        except Exception as e:
            print(e)
            await update.message.reply_text(text="لقد قام هذا المستخدم بحظر البوت")


async def decline_create_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.SUPERGROUP, Chat.GROUP]:
        user_id = int(update.callback_query.data.split(" ")[-1])
        context.user_data["create_account_user_id"] = user_id
        await update.callback_query.answer(
            text=f"قم بالرد على هذه الرسالة بسبب الرفض",
            show_alert=True,
        )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_row(
                build_back_button(f"back from decline create account {user_id}")
            ),
        )
        return DECLINE_REASON


async def decline_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.SUPERGROUP, Chat.GROUP]:
        text = "تم رفض طلبك لإنشاء حساب، السبب:\n\n"
        try:
            await context.bot.send_message(
                chat_id=context.user_data["create_account_user_id"],
                text=text + update.effective_message.text_html,
            )
        except:
            pass

        await context.bot.edit_message_reply_markup(
            chat_id=update.effective_chat.id,
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(text="تم الرفض", callback_data="تم الرفض")
            ),
            message_id=update.effective_message.reply_to_message.id,
        )

        return ConversationHandler.END


async def back_from_decline_create_account(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [Chat.SUPERGROUP, Chat.GROUP]:
        user_id = int(update.callback_query.data.split(" ")[-1])
        decline_create_account_button = [
            [
                InlineKeyboardButton(
                    text="رفض⛔️", callback_data=f"decline create account {user_id}"
                )
            ],
        ]
        await update.callback_query.answer(
            text=f"<code>{user_id}</code>\nقم بالرد على هذه الرسالة بصورة الحساب.",
            show_alert=True,
        )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(decline_create_account_button),
        )
        return ConversationHandler.END


reply_to_create_account_order_handler = MessageHandler(
    filters=filters.REPLY & Account() & filters.PHOTO,
    callback=reply_to_create_account_order,
)

decline_create_account_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(decline_create_account, "^decline create account \d+$")
    ],
    states={
        DECLINE_REASON: [MessageHandler(filters=filters.REPLY, callback=decline_reason)]
    },
    fallbacks=[
        CallbackQueryHandler(
            back_from_decline_create_account, "^back from decline create account \d+$"
        )
    ],
)

create_account_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(create_account, "^create account$")],
    states={
        FULL_NAME: [MessageHandler(filters=filters.TEXT, callback=full_name)],
        NATIONAL_NUMBER: [
            MessageHandler(filters=filters.Regex("^\d+$"), callback=national_number)
        ],
    },
    fallbacks=[CallbackQueryHandler(cancel_create_account, "^cancel create account$")],
)
