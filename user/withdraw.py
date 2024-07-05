from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Chat,
    Video,
    error,
)


from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from common.common import (
    build_user_keyboard,
    build_methods_keyboard,
    payment_method_pattern,
    build_back_button,
)

from common.decorators import check_if_user_created_account_from_bot_decorator, check_if_user_present_decorator

from common.force_join import check_if_user_member_decorator
from common.back_to_home_page import (
    back_to_user_home_page_handler,
    back_to_user_home_page_button,
)

from start import start_command

from DB import DB
import pathlib
from constants import *
import os

(
    WITHDRAW_ACCOUNT,
    PAYMENT_METHOD,
    PAYMENT_INFO,
    BANK_ACCOUNT_NAME,
    WITHDRAW_CODE,
) = range(5)


@check_if_user_present_decorator
@check_if_user_member_decorator
@check_if_user_created_account_from_bot_decorator
async def choose_withdraw_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:

        if not context.bot_data["data"]["user_calls"]["withdraw"]:
            await update.callback_query.answer("السحوبات متوقفة حالياً❗️")
            return ConversationHandler.END
        
        elif DB.check_user_pending_orders(
            order_type="withdraw",
            user_id=update.effective_user.id,
        ):
            await update.callback_query.answer("لديك طلب سحب قيد التنفيذ بالفعل ❗️")
            return ConversationHandler.END

        accounts = DB.get_user_accounts(user_id=update.effective_user.id)
        accounts_keyboard = [
            InlineKeyboardButton(
                text=a["acc_num"],
                callback_data=str(a["acc_num"]),
            )
            for a in accounts
        ]
        keybaord = [
            accounts_keyboard,
            back_to_user_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text="اختر حساباً من حساباتك المسجلة لدينا",
            reply_markup=InlineKeyboardMarkup(keybaord),
        )
        return WITHDRAW_ACCOUNT


back_to_choose_withdraw_account = choose_withdraw_account


async def choose_payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        if not update.callback_query.data.startswith("back"):
            context.user_data["withdraw_account"] = update.callback_query.data
        payment_methods = build_methods_keyboard()
        payment_methods.append(build_back_button("back_to_choose_withdraw_account"))
        payment_methods.append(back_to_user_home_page_button[0])

        await update.callback_query.edit_message_text(
            text="اختر وسيلة الدفع💳",
            reply_markup=InlineKeyboardMarkup(payment_methods),
        )
        return PAYMENT_METHOD


back_to_choose_payment_method = choose_payment_method


async def choose_payment_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:

        data = update.callback_query.data
        if not data.startswith("back"):
            method = DB.get_payment_method(name=data)
            if method[1] == 0:
                await update.callback_query.answer("هذه الوسيلة متوقفة مؤقتاً❗️")
                return

            context.user_data["payment_method"] = data

        back_keyboard = [
            build_back_button("back_to_choose_payment_method"),
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

        return PAYMENT_INFO


async def back_to_choose_payment_info(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE:
        back_keyboard = [
            build_back_button("back_to_choose_payment_method"),
            back_to_user_home_page_button[0],
        ]
        if context.user_data["payment_method"] == USDT:
            text = "أرسل كود محفظتك👝\n\n<b>ملاحظة هامة: الشبكة المستخدمه هي TRC20</b>"
        else:
            text = f"أرسل رقم حساب {context.user_data['payment_method']}"

        await update.effective_message.delete()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=InlineKeyboardMarkup(back_keyboard),
        )

        return PAYMENT_INFO


async def get_withdraw_code_bank_account_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if update.effective_chat.type == Chat.PRIVATE:
        back_keyboard = [
            build_back_button("back_to_choose_payment_info"),
            back_to_user_home_page_button[0],
        ]
        if context.user_data["payment_method"] in (BARAKAH, BEMO):
            await update.message.reply_text(
                text="أرسل اسم صاحب الحساب كما هو مسجل بالبنك.",
                reply_markup=InlineKeyboardMarkup(back_keyboard),
            )
            return BANK_ACCOUNT_NAME

        context.user_data["payment_method_number"] = update.message.text
        context.user_data["bank_account_name"] = ""

        await update.message.reply_video(
            video=os.getenv("VIDEO_ID"),
            filename="how_to_get_withdraw_code",
            caption=(
                "أرسل كود السحب\n\n" "يوضح الفيديو المرفق كيفية الحصول على الكود."
            ),
            reply_markup=InlineKeyboardMarkup(back_keyboard),
        )
        return WITHDRAW_CODE


back_to_bank_account_name = get_withdraw_code_bank_account_name


async def get_withdraw_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        if update.message:
            context.user_data["bank_account_name"] = update.message.text
        back_keyboard = [
            build_back_button("back_to_bank_account_name"),
            back_to_user_home_page_button[0],
        ]
        await update.message.reply_video(
            video=os.getenv("VIDEO_ID"),
            filename="how_to_get_withdraw_code",
            caption=(
                "أرسل كود السحب\n\n" "يوضح الفيديو المرفق كيفية الحصول على الكود."
            ),
            reply_markup=InlineKeyboardMarkup(back_keyboard),
        )
        return WITHDRAW_CODE


async def send_withdraw_order_to_check(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE:

        withdraw_code = update.message.text

        code_present = DB.check_withdraw_code(withdraw_code=withdraw_code)

        if code_present:
            back_keyboard = [
                (
                    build_back_button("back_to_bank_account_name")
                    if context.user_data["bank_account_name"]
                    else build_back_button("back_to_choose_payment_info")
                ),
                back_to_user_home_page_button[0],
            ]
            await update.message.reply_text(
                text="لقد تم إرسال هذا الكود إلى البوت من قبل ❗️",
                reply_markup=InlineKeyboardMarkup(back_keyboard),
            )
            return

        method = context.user_data["payment_method"]

        method_info = (
            f"<b>Payment info</b>: <code>{context.user_data['payment_method_number']}</code>"
            + (
                f"\nاسم صاحب الحساب: <b>{context.user_data['bank_account_name']}</b>"
                if method in [BARAKAH, BARAKAH]
                else ""
            )
        )

        serial = await DB.add_withdraw_order(
            group_id=context.bot_data["data"]["withdraw_orders_group"],
            user_id=update.effective_user.id,
            method=method,
            acc_number=context.user_data["withdraw_account"],
            withdraw_code=update.message.text,
            bank_account_name=context.user_data["bank_account_name"],
            payment_method_number=context.user_data["payment_method_number"],
        )

        account = DB.get_account(acc_num=context.user_data["withdraw_account"])

        message = await context.bot.send_message(
            chat_id=context.bot_data["data"]["withdraw_orders_group"],
            text=stringify_order(
                w_type=context.user_data.get("withdraw_type", "balance"),
                acc_number=context.user_data["withdraw_account"],
                password=account["password"],
                withdraw_code=update.message.text,
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
    withdraw_code: str,
    method: str,
    serial: int,
    method_info: str,
):
    g_b_dict = {"gift": "مكافأة", "balance": "رصيد"}
    return (
        f"تفاصيل طلب سحب {g_b_dict[w_type]}:\n\n"
        f"رقم الحساب 🔢: <code>{acc_number}</code>\n"
        f"كلمة المرور 🈴: <code>{password}</code>\n"
        f"كود السحب: <code>{withdraw_code}</code>\n"
        f"وسيلة الدفع💳: <b>{method}</b>\n\n"
        f"Serial: <code>{serial}</code>\n\n"
        f"{method_info}\n\n"
        f"تحقق من توفر المبلغ وقم بقبول/رفض الطلب بناء على ذلك.\n"
    )


withdraw_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            choose_withdraw_account,
            "^withdraw$",
        ),
    ],
    states={
        WITHDRAW_ACCOUNT: [
            CallbackQueryHandler(
                choose_payment_method,
                "^\d+$",
            ),
        ],
        PAYMENT_METHOD: [
            CallbackQueryHandler(
                choose_payment_info,
                payment_method_pattern,
            )
        ],
        PAYMENT_INFO: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=get_withdraw_code_bank_account_name,
            )
        ],
        BANK_ACCOUNT_NAME: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=get_withdraw_code,
            )
        ],
        WITHDRAW_CODE: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=send_withdraw_order_to_check,
            )
        ],
    },
    fallbacks=[
        CallbackQueryHandler(
            back_to_choose_withdraw_account,
            "^back_to_choose_withdraw_account$",
        ),
        CallbackQueryHandler(
            back_to_choose_payment_method,
            "^back_to_choose_payment_method$",
        ),
        CallbackQueryHandler(
            back_to_choose_payment_info,
            "^back_to_choose_payment_info$",
        ),
        CallbackQueryHandler(
            back_to_bank_account_name,
            "^back_to_bank_account_name$",
        ),
        back_to_user_home_page_handler,
        start_command,
    ],
    name="withdraw_handler",
    persistent=True,
)
