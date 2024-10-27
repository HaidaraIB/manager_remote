from telegram.ext import ContextTypes
import models
from common.common import format_amount, format_datetime, parent_to_child_models_mapper
from common.constants import *

state_dict_en_to_ar = {
    "declined": "مرفوض",
    "approved": "تمت الموافقة",
    "returned": "طلب معاد",
    "pending": "بانتظار التحقق",
    "sent": "بانتظار التنفيذ",
    "checking": "قيد التحقق",
    "processing": "قيد التنفيذ",
    "deleted": "محذوف",
    "canceled": "ملغى",
    "split": "مرتجع",
}

worker_type_dict = {
    "daily": {
        "approved_work": "approved_withdraws_day",
        "percentage": "workers_reward_withdraw_percentage",
        "role": "withdraws",
        "day_week": {
            "ar": "اليوم",
            "en": "day",
        },
        "model": models.PaymentAgent,
    },
    "weekly": {
        "approved_work": "approved_deposits_week",
        "percentage": "workers_reward_percentage",
        "role": "deposits",
        "day_week": {"ar": "الأسبوع", "en": "week"},
        "model": models.DepositAgent,
    },
}


def stringify_wallet(wallet: models.Wallet):
    return (
        "معلومات المحفظة:\n"
        f"الوسيلة: {wallet.method}\n"
        f"الرقم: <code>{wallet.number}</code>\n"
        f"الرصيد: <b>{format_amount(wallet.balance)}</b>\n"
        f"الحد المسموح: <b>{format_amount(wallet.limit)}</b>"
    )


def stringify_agent(agent: models.TrustedAgent):
    text = (
        "معلومات الوكيل:\n"
        f"الآيدي: <code>{agent.user_id}</code>\n"
        f"المحافظة: <b>{agent.gov}</b>\n"
        f"الحي: <code>{agent.neighborhood}</code>\n\n"
        f"Workplace ID: <code>{agent.team_cash_workplace_id}</code>\n"
        f"Team Cash User ID: <code>{agent.team_cash_user_id}</code>\n"
        f"Team Cash Password: <code>{agent.team_cash_password}</code>\n\n"
        f"Promo Username: <code>{agent.promo_username}</code>\n"
        f"Promo Password: <code>{agent.promo_password}</code>\n\n"
    )
    return text


def stringify_manager_reward_report(
    worker: models.DepositAgent | models.PaymentAgent,
    updated_worker: models.DepositAgent | models.PaymentAgent,
    amount: float,
    reward_type: str,
):
    manager_text = (
        f"تم تحديث رصيد المكافآت عن مجموع مبالغ الطلبات الناجحة للموظف:\n\n"
        f"id: <code>{worker.id}</code>\n"
        f"name: <b>{worker.name}</b>\n"
        f"username: {'@' + worker.username if worker.username else '<b>لا يوجد</b>'}\n\n"
    )
    return manager_text + stringify_reward_report(
        worker=worker,
        updated_worker=updated_worker,
        amount=amount,
        reward_type=reward_type,
    )


def stringify_reward_report(
    worker: models.DepositAgent | models.PaymentAgent,
    updated_worker: models.DepositAgent | models.PaymentAgent,
    amount: float,
    reward_type: str,
):
    role = worker_type_dict[reward_type]["role"]
    balance = updated_worker.__getattribute__(f"approved_{role}")
    partial_balance = worker.__getattribute__(
        f"approved_{role}_{worker_type_dict[reward_type]['day_week']['en']}"
    )
    prev_rewards_balance = worker.__getattribute__(f"{reward_type}_rewards_balance")
    rewards_balance = updated_worker.__getattribute__(f"{reward_type}_rewards_balance")
    orders_num = updated_worker.__getattribute__(f"approved_{role}_num")
    work_type = worker_type_dict[reward_type]["day_week"]["ar"]

    worker_text = (
        f"الوظيفة: {f'سحب {updated_worker.method}' if role == 'withdraws' else 'تنفيذ إيداع'}\n"
        f"مجموع المكافآت السابق: <b>{format_amount(prev_rewards_balance)}</b>\n"
        f"قيمة المكافأة: <b>{format_amount(amount)}</b>\n"
        f"مجموع المكافآت الحالي: <b>{format_amount(rewards_balance)}</b>\n"
        f"عدد الطلبات حتى الآن: <b>{orders_num}</b>\n"
        f"مجموع المبالغ حتى الآن: <b>{format_amount(balance)}</b>\n"
        f"مجموع المبالغ هذا {work_type}: <b>{format_amount(partial_balance)}</b>\n"
    )
    worker_text += (
        f"الدفعات المسبقة:\n<b>{format_amount(worker.pre_balance)}</b>\n"
        if isinstance(worker, models.PaymentAgent)
        else ""
    )

    return worker_text


order_settings_dict: dict[
    str, dict[str, models.WithdrawOrder | models.DepositOrder | models.BuyUsdtdOrder]
] = {
    "withdraw": {"cls": models.WithdrawOrder, "t": "سحب"},
    "deposit": {"cls": models.DepositOrder, "t": "إيداع"},
    "busdt": {"cls": models.BuyUsdtdOrder, "t": "شراء USDT"},
}


def general_stringify_order(serial: int, order_type: str, name: str):
    order = parent_to_child_models_mapper[order_type].get_one_order(serial=serial)
    return (
        f"تفاصيل الطلب:\n\n"
        f"الرقم التسلسلي: <code>{order.serial}</code>\n\n"
        f"آيدي المستخدم صاحب الطلب: <code>{order.user_id}</code>\n"
        f"اسمه: <b>{name}</b>\n\n"
        f"آيدي الوكيل: <code>{getattr(order, 'agent_id', 'لا يوجد')}</code>\n"
        f"آيدي موظف التحقق: <code>{order.checker_id}</code>\n"
        f"آيدي موظف الدفع: <code>{order.worker_id}</code>\n\n"
        f"نوع الطلب: <b>{order_settings_dict[order_type]['t']}</b>\n"
        f"المبلغ: <code>{format_amount(order.amount)}</code>\n"
        f"رقم الحساب: <code>{getattr(order, 'acc_number', 'لا يوجد')}</code>\n"
        f"كود السحب: <code>{getattr(order, 'withdraw_code', 'لا يوجد')}</code>\n\n"
        f"وسيلة الدفع: <code>{order.method}</code>\n"
        f"محفظة الإيداع: <code>{getattr(order, 'deposit_wallet', 'لا يوجد')}</code>\n"
        f"رقم العملية: <code>{getattr(order, 'ref_number', 'لا يوجد')}</code>\n\n"
        f"الحالة: <b>{state_dict_en_to_ar[order.state]}</b>\n"
        f"سبب رفض: <b>{'\n' + order.reason if order.reason else 'لا يوجد'}</b>\n\n"
        f"جاري العمل عليه: <b>{'نعم' if order.working_on_it else 'لا'}</b>\n"
        f"تم إغلاق شكوى عنه : <b>{'نعم' if order.complaint_took_care_of else 'لا'}</b>\n\n"
        f"تاريخ الإنشاء:\n<b>{format_datetime(order.order_date)}</b>\n\n"
        f"تاريخ الإرسال: <b>{'\n' + format_datetime(order.send_date) if order.send_date else 'لا يوجد'}</b>\n\n"
        f"تاريخ الموافقة: <b>{'\n' + format_datetime(order.approve_date) if order.approve_date else 'لا يوجد'}</b>\n\n"
        f"تاريخ الرفض: <b>{'\n' + format_datetime(order.decline_date) if order.decline_date else 'لا يوجد'}</b>\n\n"
        f"تاريخ الإعادة: <b>{'\n' + format_datetime(order.return_date) if order.return_date else 'لا يوجد'}</b>\n\n"
        f"تاريخ الرفض: <b>{'\n' + format_datetime(order.delete_date) if order.delete_date else 'لا يوجد'}</b>\n\n"
    )


def user_stringify_order(serial: int, order_type: str):
    op = parent_to_child_models_mapper[order_type].get_one_order(serial=serial)
    payment_method_number = "لا يوجد"
    if order_type != "deposit":
        payment_method_number = (
            op.payment_method_number if op.payment_method_number else "لا يوجد"
        )

    return (
        f"نوع الطلب: <b>{order_settings_dict[order_type]['t']}</b>\n"
        f"الرقم التسلسلي: <code>{op.serial}</code>\n"
        f"المبلغ: <b>{format_amount(op.amount)}</b>\n"
        f"وسيلة الدفع: <b>{op.method}</b>\n"
        f"عنوان الدفع: <code>{payment_method_number}</code>\n"
        f"الحالة: <b>{state_dict_en_to_ar[op.state]}</b>\n"
        f"سبب رفض: <b>{op.reason if op.reason else 'لا يوجد'}</b>\n\n"
    )


def stringify_w_with_us_order(
    gov: str,
    neighborhood: str,
    email: str,
    phone: str,
    amount: float,
    ref_num: str,
    serial: int,
):
    return (
        f"المحافظة: <b>{gov}</b>\n"
        f"الحي: <b>{neighborhood}</b>\n"
        f"الإيميل: <b>{email}</b>\n"
        f"رقم الهاتف: <b>{phone}</b>\n"
        f"المبلغ: <code>{amount}</code>\n"
        f"رقم العملية: <code>{ref_num}</code>\n"
        f"Serial: <code>{serial}</code>"
    )


def stringify_deposit_order(
    amount: float,
    serial: int,
    method: str,
    account_number: int = "لا يوجد",
    wal: str = "لا يوجد",
    ref_num: str = "لا يوجد",
    workplace_id: int = None,
    *args,
):
    deposit_order_text = (
        "إيداع جديد:\n"
        f"رقم العملية: <code>{ref_num}</code>\n"
        f"المبلغ 💵: <code>{amount if amount else 'لا يوجد بعد'}</code>\n"
        f"رقم الحساب: <code>{account_number}</code>\n\n"
        f"وسيلة الدفع: <code>{method}</code>\n"
        f"المحفظة: <code>{wal}</code>\n\n"
        f"Serial: <code>{serial}</code>\n\n"
    )
    if workplace_id:
        deposit_order_text += f"Workplace id: <code>{workplace_id}</code>\n\n"
    return (
        deposit_order_text
        + "تنبيه: اضغط على رقم الحساب والمبلغ لنسخها كما هي في الرسالة تفادياً للخطأ."
    )


def stringify_check_withdraw_order(
    acc_number: int,
    password: str,
    withdraw_code: str,
    method: str,
    serial: int,
    method_info: str,
):
    return (
        "تفاصيل طلب سحب رصيد:\n\n"
        f"رقم الحساب 🔢: <code>{acc_number}</code>\n"
        f"كلمة المرور 🈴: <code>{password if password else 'لا يوجد'}</code>\n"
        f"كود السحب: <code>{withdraw_code}</code>\n"
        f"وسيلة الدفع 💳: <b>{method}</b>\n\n"
        f"Serial: <code>{serial}</code>\n\n"
        f"{method_info}\n\n"
        f"تحقق من توفر المبلغ وقم بقبول/رفض الطلب بناء على ذلك.\n\n"
        "<b><i>ملاحظة:</i></b> عند عدم وجود كلمة مرور فالطلب مقدم من قبل وكيل والحساب لم يتم إنشاؤه عن طريق البوت."
    )


def stringify_process_withdraw_order(
    amount: float,
    serial: int,
    method: str,
    payment_method_number: str,
    *args,
):
    return (
        "تفاصيل طلب سحب :\n\n"
        f"المبلغ 💵: <code>{amount if amount else 'لا يوجد بعد'}</code>\n\n"
        f"Serial: <code>{serial}</code>\n\n"
        f"وسيلة الدفع: <code>{method}</code>\n\n"
        f"Payment Info: <code>{payment_method_number}</code>\n\n"
        "تنبيه: اضغط على رقم المحفظة والمبلغ لنسخها كما هي في الرسالة تفادياً للخطأ."
    )


def stringify_check_busdt_order(amount, method, serial, method_info):
    return (
        f"طلب شراء USDT جديد:\n\n"
        f"المبلغ💵: <code>{amount}</code> USDT\n"
        f"وسيلة الدفع 💳: <b>{method}</b>\n\n"
        f"Serial: <code>{serial}</code>\n\n"
        f"{method_info}\n"
    )


def stringify_process_busdt_order(
    amount: float,
    serial: int,
    method: str,
    payment_method_number: str,
    *args,
):
    return (
        "طلب شراء USDT جديد:\n\n"
        f"المبلغ 💵: <code>{amount if amount else 'لا يوجد بعد'}</code>\n\n"
        f"Serial: <code>{serial}</code>\n\n"
        f"وسيلة الدفع: <code>{method}</code>\n\n"
        f"Payment Info: <code>{payment_method_number}</code>\n\n"
        "تنبيه: اضغط على رقم المحفظة والمبلغ لنسخها كما هي في الرسالة تفادياً للخطأ."
    )


def stringify_daily_order_stats(type_: str, stats):
    stats_by_method_text = ""
    for s in stats:
        stats_by_method_text += f"{s[0]}: <b>{format_amount(s[1])}</b>\n"

    amounts_sum = sum(list(map(lambda x: float(x[1]), stats)))
    methods_amounts_sum = sum(
        list(
            map(
                lambda x: (
                    float(x[1])
                    if x[0] not in [CREATE_ACCOUNT_DEPOSIT, GHAFLA_OFFER]
                    else 0
                ),
                stats,
            )
        )
    )

    return (
        f"مجموع {type_} اليوم الكلي: <b>{format_amount(amounts_sum)}</b>\n"
        f"مجموع {type_} اليوم بدون العروض: <b>{format_amount(methods_amounts_sum)}</b>\n\n"
        "<i>التفاصيل:</i>\n" + stats_by_method_text
    )


def stringify_daily_wallet_stats(method: str, stats: list[models.Wallet]):
    wallet_stats_text = ""
    for s in stats:
        wallet_stats_text += f"{s.number}: <b>{format_amount(s.balance)}</b>\n"

    amounts_sum = sum(list(map(lambda x: x.balance, stats)))

    return (
        f"أرصدة محافظ {method}: \n\n"
        + wallet_stats_text
        + f"\nالمجموع: <b>{format_amount(amounts_sum)}</b>"
    )


async def create_order_user_info_line(user_id:int, context:ContextTypes.DEFAULT_TYPE):
    try:
        tg_user = await context.bot.get_chat(chat_id=user_id)
    except:
        tg_user = models.User.get_user(user_id=user_id)
    return f"\n\nصاحب الطلب: {"@" + tg_user.username if tg_user.username else (tg_user.name if isinstance(tg_user, models.User) else tg_user.full_name)}\n\n"


def stringify_account(account:models.Account):
    return (
        f"رقم الحساب: <code>{account.acc_num}</code>\n"
        f"كلمة المرور: <code>{account.password}</code>"
    ) + (f"\nقيمة الهدية: <b>{account.deposit_gift}</b>" if account.deposit_gift else "")
