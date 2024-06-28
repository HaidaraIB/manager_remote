from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Chat,
)


from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from custom_filters.User import User

from common.common import (
    build_user_keyboard,
    build_methods_keyboard,
    payment_method_pattern,
    build_back_button,
)

from common.force_join import check_if_user_member_decorator
from common.back_to_home_page import (
    back_to_user_home_page_handler,
    back_to_user_home_page_button,
)

from start import start_command

from DB import DB

from constants import *

(
    AMOUNT,
    PAYMENT_METHOD,
    WALLET_CODE,
    BANK_NUMBER_WITHDRAW,
    BANK_ACCOUNT_NAME,
    ACCOUNT_NUMBER,
    PASSWORD,
    LAST_NAME,
) = range(8)


withdraw_type_keyboard = [
    [
        InlineKeyboardButton(text="سحب مكافآت🎁", callback_data="withdraw gift"),
        InlineKeyboardButton(text="سحب رصيد👝", callback_data="withdraw balance"),
    ],
    back_to_user_home_page_button[0],
]


@check_if_user_member_decorator
async def withdraw_section(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):

        user = DB.get_user(user_id=update.effective_user.id)
        if not user:
            new_user = update.effective_user
            await DB.add_new_user(
                user_id=new_user.id, username=new_user.username, name=new_user.full_name
            )

        if not context.bot_data["data"]["user_calls"]["withdraw"]:
            await update.callback_query.answer("السحوبات متوقفة حالياً❗️")
            return ConversationHandler.END

        await update.callback_query.edit_message_text(
            text="اختر ما الذي تريد سحبه❔",
            reply_markup=InlineKeyboardMarkup(withdraw_type_keyboard),
        )


async def withdraw_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        context.user_data["withdraw_type"] = update.callback_query.data.split(" ")[-1]
        back_buttons = [
            build_back_button("back to withdraw section"),
            back_to_user_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text="أرسل المبلغ المراد سحبه💵",
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return AMOUNT


async def back_to_withdraw_section(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):

        await update.callback_query.edit_message_text(
            text="اختر ما الذي تريد سحبه❔",
            reply_markup=InlineKeyboardMarkup(withdraw_type_keyboard),
        )
        return ConversationHandler.END


async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        amount = float(update.message.text)
        context.user_data["withdrawal_amount"] = amount

        user = DB.get_user(user_id=update.effective_user.id)
        if (user[4] < amount or user[4] < 10_000) and context.user_data[
            "withdraw_type"
        ] == "withdraw gift":
            text = (
                f"❌ عذراً يا عزيزي رصيد مكافآتك غير كافي لعملية السحب.\n\n"
                f"🎁 رصيد مكافآتك الحالي هو: <b>{user[4]}$</b>\n"
                f"Ⓜ️ الحد الأدنى للسحب: <b>10000$</b>\n"
                f"📤 المبلغ المراد سحبه: <b>{amount}$</b>\n"
            )
            await update.message.reply_text(
                text=text,
                reply_markup=build_user_keyboard(),
            )

            return ConversationHandler.END

        payment_methods = build_methods_keyboard()
        payment_methods.append(build_back_button("back to withdraw type"))
        payment_methods.append(back_to_user_home_page_button[0])

        await update.message.reply_text(
            text="اختر وسيلة الدفع💳",
            reply_markup=InlineKeyboardMarkup(payment_methods),
        )
        return PAYMENT_METHOD


back_to_withdraw_type = withdraw_type


async def payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):

        data = update.callback_query.data
        if not data.startswith("back"):
            method = DB.get_payment_method(name=data)
            if method[1] == 0:
                await update.callback_query.answer("هذه الوسيلة متوقفة مؤقتاً❗️")
                return

            context.user_data["payment_method"] = data

        back_keyboard = [
            build_back_button("back to payment method"),
            back_to_user_home_page_button[0],
        ]
        if context.user_data["payment_method"] == USDT:
            text = "أرسل كود محفظتك👝\n\n<b>ملاحظة هامة: الشبكة المستخدمه هي TRC20</b>"
        else:
            text = f"أرسل رقم حساب {data}"

        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(back_keyboard),
        )

        if context.user_data["payment_method"] in [BEMO, BARAKAH]:
            return BANK_NUMBER_WITHDRAW
        return WALLET_CODE


async def back_to_withdraw_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        back_buttons = [
            build_back_button("back to withdraw type"),
            back_to_user_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text="أرسل المبلغ المراد سحبه💵",
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return AMOUNT


async def bank_number_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        back_keyboard = [
            build_back_button("back to bank number withdraw"),
            back_to_user_home_page_button[0],
        ]
        context.user_data["payment_method_number"] = update.message.text

        await update.message.reply_text(
            text="أرسل اسم صاحب الحساب كما هو مسجل بالبنك.",
            reply_markup=InlineKeyboardMarkup(back_keyboard),
        )
        return BANK_ACCOUNT_NAME


async def back_to_payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        payment_methods = build_methods_keyboard()
        payment_methods.append(build_back_button("back to withdraw type"))
        payment_methods.append(back_to_user_home_page_button[0])

        await update.callback_query.edit_message_text(
            text="اختر وسيلة الدفع💳",
            reply_markup=InlineKeyboardMarkup(payment_methods),
        )
        return PAYMENT_METHOD


async def wallet_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        if context.user_data["payment_method"] in (
            USDT,
            SYRCASH,
            MTNCASH,
        ):
            context.user_data["payment_method_number"] = update.message.text
            context.user_data["bank_account_name"] = ""
        else:
            context.user_data["bank_account_name"] = update.message.text

        back_keyboard = [
            (
                build_back_button("back to payment method")
                if context.user_data["payment_method"] not in [BEMO, BARAKAH]
                else build_back_button("back to bank account name")
            ),
            back_to_user_home_page_button[0],
        ]
        await update.message.reply_text(
            text="أرسل رقم حسابك🔢", reply_markup=InlineKeyboardMarkup(back_keyboard)
        )
        return ACCOUNT_NUMBER


async def back_to_bank_number_withdraw(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        back_keyboard = [
            build_back_button("back to payment method"),
            back_to_user_home_page_button[0],
        ]
        name = "بركة" if context.user_data["payment_method"] == BARAKAH else "بيمو"
        await update.callback_query.edit_message_text(
            text=f"أرسل رقم حساب {name} 👝",
            reply_markup=InlineKeyboardMarkup(back_keyboard),
        )
        return BANK_NUMBER_WITHDRAW


bank_account_name = wallet_code


async def back_to_bank_account_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        back_keyboard = [
            build_back_button("back to bank number withdraw"),
            back_to_user_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text="أرسل اسم صاحب الحساب كما هو مسجل بالبنك.",
            reply_markup=InlineKeyboardMarkup(back_keyboard),
        )
        return BANK_ACCOUNT_NAME


back_to_payment_info = payment_method


async def account_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        context.user_data["account_number"] = update.message.text

        back_keyboard = [
            build_back_button("back to account number"),
            back_to_user_home_page_button[0],
        ]
        await update.message.reply_text(
            text="أرسل كلمة مرور حسابك🈴",
            reply_markup=InlineKeyboardMarkup(back_keyboard),
        )
        return PASSWORD


async def back_to_account_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        back_keyboard = [
            build_back_button("back to payment info"),
            back_to_user_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text="أرسل رقم حسابك🔢", reply_markup=InlineKeyboardMarkup(back_keyboard)
        )
        return ACCOUNT_NUMBER


async def get_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        context.user_data["password"] = update.message.text
        back_keyboard = [
            build_back_button("back to password"),
            back_to_user_home_page_button[0],
        ]
        await update.message.reply_text(
            text="أرسل الكنية/العائلة🔤",
            reply_markup=InlineKeyboardMarkup(back_keyboard),
        )
        return LAST_NAME


async def back_to_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        back_keyboard = [
            build_back_button("back to account number"),
            back_to_user_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text="أرسل كلمة مرور حسابك🈴",
            reply_markup=InlineKeyboardMarkup(back_keyboard),
        )
        return PASSWORD


async def get_last_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):

        amount = context.user_data["withdrawal_amount"]

        if context.user_data["withdraw_type"] == "withdraw gift":
            await DB.update_gifts_balance(
                user_id=update.effective_user.id, amount=-amount
            )

        method = context.user_data["payment_method"]

        method_info = f"<b>Payment info</b>: <code>{context.user_data['payment_method_number']}</code>"
        method_info += (
            f"\nاسم صاحب الحساب: <b>{context.user_data['bank_account_name']}</b>"
            if method in [BARAKAH, BARAKAH]
            else ""
        )

        serial = await DB.add_withdraw_order(
            group_id=context.bot_data["data"]["withdraw_orders_group"],
            user_id=update.effective_user.id,
            method=method,
            acc_number=context.user_data["account_number"],
            password=context.user_data["password"],
            last_name=update.message.text,
            amount=amount,
            bank_account_name=context.user_data["bank_account_name"],
            payment_method_number=context.user_data["payment_method_number"],
        )

        message = await context.bot.send_message(
            chat_id=context.bot_data["data"]["withdraw_orders_group"],
            text=stringify_order(
                w_type=context.user_data["withdraw_type"],
                acc_number=context.user_data["account_number"],
                password=context.user_data["password"],
                last_name=update.message.text,
                amount=amount,
                method=method,
                serial=serial,
                method_info=method_info,
            ),
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="التحقق☑️", callback_data=f"check_withdraw_order_{serial}"
                )
            ),
        )

        await DB.add_message_ids(
            order_type="withdraw",
            serial=serial,
            pending_check_message_id=message.id,
        )

        await update.message.reply_text(
            text="شكراً لك، تم إرسال طلبك إلى قسم المراجعة، سيصلك رد خلال وقت قصير.",
            reply_markup=build_user_keyboard(),
        )

        return ConversationHandler.END


def stringify_order(
    w_type: str,
    acc_number: int,
    password: str,
    last_name: str,
    amount: float,
    method: str,
    serial: int,
    method_info: str,
):
    g_b_dict = {"gift": "مكافأة", "balance": "رصيد"}
    return (
        f"تفاصيل طلب سحب {g_b_dict[w_type]}:\n\n"
        f"رقم حسابه🔢: <code>{acc_number}</code>\n"
        f"كلمة المرور🈴: <code>{password}</code>\n"
        f"الكنية: <code>{last_name}</code>\n\n"
        f"المبلغ💵: <code>{amount}</code>\n"
        f"وسيلة الدفع💳: <b>{method}</b>\n\n"
        f"Serial: <code>{serial}</code>\n\n"
        f"{method_info}\n\n"
        f"تحقق من توفر المبلغ وقم بقبول/رفض الطلب بناء على ذلك.\n"
    )


withdraw_section_handler = CallbackQueryHandler(withdraw_section, "^withdraw$")

withdraw_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(withdraw_type, "^withdraw gift$|^withdraw balance$")
    ],
    states={
        PAYMENT_METHOD: [CallbackQueryHandler(payment_method, payment_method_pattern)],
        WALLET_CODE: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND, callback=wallet_code
            )
        ],
        BANK_ACCOUNT_NAME: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND, callback=bank_account_name
            )
        ],
        BANK_NUMBER_WITHDRAW: [
            MessageHandler(
                filters=filters.Regex(".*") & ~filters.COMMAND,
                callback=bank_number_withdraw,
            )
        ],  # TODO add a regex
        AMOUNT: [
            MessageHandler(
                filters=filters.Regex("^[1-9]+\.?\d*$") & ~filters.COMMAND,
                callback=get_amount,
            )
        ],
        ACCOUNT_NUMBER: [
            MessageHandler(filters=filters.Regex("^\d+$"), callback=account_number)
        ],
        PASSWORD: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND, callback=get_password
            )
        ],
        LAST_NAME: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND, callback=get_last_name
            )
        ],
    },
    fallbacks=[
        CallbackQueryHandler(back_to_payment_method, "^back to payment method$"),
        CallbackQueryHandler(back_to_withdraw_amount, "^back to withdraw amount$"),
        CallbackQueryHandler(back_to_bank_account_name, "^back to bank account name$"),
        CallbackQueryHandler(
            back_to_bank_number_withdraw, "^back to bank number withdraw$"
        ),
        CallbackQueryHandler(back_to_withdraw_section, "^back to withdraw section$"),
        CallbackQueryHandler(back_to_password, "^back to password$"),
        CallbackQueryHandler(back_to_account_number, "^back to account number$"),
        CallbackQueryHandler(back_to_payment_info, "^back to peyment info$"),
        CallbackQueryHandler(back_to_withdraw_type, "^back to withdraw type$"),
        back_to_user_home_page_handler,
        start_command,
    ],
    name="withdraw_handler",
    persistent=True,
)
