from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    Application,
    PicklePersistence,
    InvalidCallbackData,
    Defaults,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.constants import ParseMode
from ptbcontrib.ptb_jobstores.sqlalchemy import PTBSQLAlchemyJobStore
from PyroClientSingleton import PyroClientSingleton
from start import (
    start_command,
    admin_command,
    worker_command,
    error_command,
    end_offer_command,
    inits,
)
from jobs import (
    reward_worker,
    remind_agent_to_clear_wallets,
    schedule_ghafla_offer_jobs,
    schedule_lucky_hour_jobs,
    send_daily_stats,
)
from common.common import invalid_callback_data, create_folders
from common.constants import TIMEZONE
from common.error_handler import error_handler
from common.force_join import check_joined_handler
from common.back_to_home_page import (
    back_to_user_home_page_handler,
    back_to_admin_home_page_handler,
)

from agent.login import *

from user.referral import *
from user.withdraw import *
from user.deposit import *
from user.busdt import *
from user.return_order import *
from user.accounts_settings import *
from user.work_with_us import *
from user.show_trusted_agents import *
from user.complaint import *
from user.respond_to_contact_msg import *
from user.user_settings import *

from admin.offers import *
from admin.stats import *
from admin.admin_calls import *
from admin.admin_settings import *
from admin.wallet_settings import *
from admin.rewards_settings import *
from admin.broadcast import *
from admin.groups_settings import *
from admin.workers_settings import *
from admin.order_settings import *
from admin.exchange_rates import *
from admin.agent_settings import *
from admin.restart import restart_handler

from worker.request_order import *
from worker.process_deposit import *
from worker.check_withdraw import *
from worker.process_withdraw import *
from worker.check_busdt import *
from worker.process_busdt import *
from worker.check_deposit import *
from worker.create_account import *
from worker.contact_dev import *

from agent.player_deposit import *
from agent.player_withdraw import *
from agent.point_deposit import *

from check_complaint import *

from check_work_with_us import *

from dotenv import load_dotenv

import datetime
import pytz
import os
import sys
from models import create_tables


async def get_file_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        msg = update.message
        if msg.document:
            print(msg.document.file_id)
        elif msg.video:
            print(msg.video.file_id)
        elif msg.photo:
            print(msg.photo[-1].file_id)
        elif msg.audio:
            print(msg.audio.file_id)
    except:
        pass


def main():
    create_folders()
    load_dotenv()
    create_tables()
    defaults = Defaults(parse_mode=ParseMode.HTML)
    my_persistence = PicklePersistence(
        filepath=os.getenv("PERSISTENCE_PATH"), single_file=False
    )
    app = (
        Application.builder()
        .token(os.getenv("BOT_TOKEN"))
        .post_init(inits)
        .persistence(persistence=my_persistence)
        .defaults(defaults)
        .concurrent_updates(True)
        .build()
    )

    app.job_queue.scheduler.add_jobstore(
        PTBSQLAlchemyJobStore(
            application=app,
            url=os.getenv("JOB_STORE_PATH"),
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            callback=invalid_callback_data, pattern=InvalidCallbackData
        )
    )

    # AGENT
    app.add_handler(player_deposit_handler)
    app.add_handler(player_withdraw_handler)
    app.add_handler(point_deposit_handler)

    app.add_handler(show_trusted_agents_handler)

    # DEPOSIT
    app.add_handler(reply_with_payment_proof_handler)
    app.add_handler(user_deposit_verified_handler)

    app.add_handler(ignore_deposit_order_handler)

    app.add_handler(return_deposit_order_handler)
    app.add_handler(return_deposit_order_reason_handler)
    app.add_handler(back_from_return_deposit_order_handler)

    app.add_handler(return_deposit_order_handler)
    app.add_handler(store_ref_number_handler, group=1)
    app.add_handler(invalid_ref_format_handler, group=1)

    app.add_handler(manual_deposit_check_handler)

    # app.add_handler(check_deposit_handler)
    # app.add_handler(get_new_amount_handler)
    # app.add_handler(send_deposit_order_handler)
    # app.add_handler(edit_deposit_amount_handler)
    # app.add_handler(decline_deposit_order_handler)
    # app.add_handler(decline_deposit_order_reason_handler)
    # app.add_handler(back_from_decline_deposit_order_handler)

    # WITHDRAW
    app.add_handler(check_withdraw_handler)
    app.add_handler(send_withdraw_order_handler)
    app.add_handler(decline_withdraw_order_handler)
    app.add_handler(back_to_withdraw_check_handler)
    app.add_handler(decline_withdraw_order_reason_handler)
    app.add_handler(get_withdraw_order_amount_handler)

    app.add_handler(user_payment_verified_handler)
    app.add_handler(reply_with_payment_proof_withdraw_handler)

    app.add_handler(return_withdraw_order_handler)
    app.add_handler(return_withdraw_order_reason_handler)
    app.add_handler(back_from_return_withdraw_order_handler)

    # BUY_USDT
    app.add_handler(check_busdt_handler)
    app.add_handler(send_busdt_order_handler)
    app.add_handler(decline_busdt_order_handler)
    app.add_handler(decline_busdt_order_reason_handler)
    app.add_handler(back_from_decline_busdt_order_handler)

    app.add_handler(reply_with_payment_proof_busdt_handler)
    app.add_handler(user_payment_verified_busdt_handler)

    app.add_handler(return_busdt_order_handler)
    app.add_handler(return_busdt_order_reason_handler)
    app.add_handler(back_from_return_busdt_order_handler)

    # CREATE ACCOUNT
    app.add_handler(accounts_count_hanlder)

    # RETURN
    app.add_handler(handle_returned_order_handler)

    app.add_handler(work_with_us_handler)

    # ADMIN SETTINGS
    app.add_handler(admin_settings_handler)
    app.add_handler(show_admins_handler)
    app.add_handler(add_admin_handler)
    app.add_handler(remove_admin_handler)

    # REWARDS SETTINGS
    app.add_handler(update_percentages_handler)
    app.add_handler(update_percentage_handler)

    # COMPLAINT
    app.add_handler(handle_respond_to_user_complaint_handler)
    app.add_handler(handle_edit_amount_user_complaint_handler)
    app.add_handler(back_from_respond_to_user_complaint_handler)
    app.add_handler(back_from_mod_amount_user_complaint_handler)
    app.add_handler(edit_order_amount_user_complaint_handler)
    app.add_handler(send_to_worker_user_complaint_handler)
    app.add_handler(respond_to_user_complaint_handler)
    app.add_handler(back_from_close_complaint_handler)
    app.add_handler(reply_on_close_complaint_handler)
    app.add_handler(skip_close_complaint_handler)
    app.add_handler(close_complaint_handler)
    app.add_handler(reply_to_returned_complaint_handler)
    app.add_handler(correct_returned_complaint_handler)
    app.add_handler(back_from_reply_to_returned_complaint_handler)

    # WORK_WITH_US
    # Agent_Orders
    app.add_handler(login_agent_handler)
    app.add_handler(notify_agent_order_handler)
    app.add_handler(accept_agent_order_handler)
    app.add_handler(get_login_info_handler)
    app.add_handler(decline_agent_order_handler)
    app.add_handler(get_decline_agent_order_reason_handler)
    app.add_handler(back_to_check_agent_order_handler)

    app.add_handler(accounts_settings_handler)
    app.add_handler(create_account_handler)
    app.add_handler(delete_account_handler)
    app.add_handler(show_account_handler)
    app.add_handler(back_to_accounts_settings_handler)
    app.add_handler(store_account_handler)
    app.add_handler(invalid_account_format_handler, group=3)

    app.add_handler(withdraw_settings_handler)
    app.add_handler(withdraw_handler)
    app.add_handler(manage_pending_withdraws_handler)

    app.add_handler(busdt_handler)

    app.add_handler(deposit_handler)

    app.add_handler(complaint_handler)

    app.add_handler(referral_handler)

    app.add_handler(user_settings_handler)

    # GROUPS SETTINGS
    app.add_handler(change_group_handler)

    # ADMIN CALLS
    app.add_handler(update_exchange_rates_handler)
    app.add_handler(turn_user_calls_on_or_off_handler)
    app.add_handler(turn_payment_method_on_or_off_handler)

    # STATS
    app.add_handler(stats_handler)
    app.add_handler(choose_stats_handler)

    app.add_handler(add_wallet_handler)
    app.add_handler(remove_wallet_handler)
    app.add_handler(show_wallet_handler)
    app.add_handler(update_wallet_handler)
    app.add_handler(wallet_settings_handler)
    app.add_handler(clear_wallets_handler)
    app.add_handler(back_to_choose_wallet_settings_option_handler)

    app.add_handler(broadcast_message_handler)

    app.add_handler(request_order_handler)

    app.add_handler(offers_handler)

    # WORKER SETTINGS
    app.add_handler(worker_balance_handler)
    app.add_handler(worker_settings_handler)
    app.add_handler(add_worker_cp_handler)
    app.add_handler(remove_worker_handler)
    app.add_handler(show_worker_handler)

    # AGENT SETTINGS
    app.add_handler(agent_settings_handler)
    app.add_handler(remove_agent_handler)
    app.add_handler(show_agent_handler)

    # ORDER SETTINGS
    app.add_handler(order_settings_handler)
    app.add_handler(edit_order_amount_handler)
    app.add_handler(request_photos_handler)
    app.add_handler(request_returned_conv_handler)
    app.add_handler(return_order_to_worker_handler)
    app.add_handler(unset_working_on_it_handler)
    app.add_handler(delete_order_handler)

    app.add_handler(contact_user_handler)
    app.add_handler(respond_to_contact_msg_handler)

    app.add_handler(check_joined_handler)

    app.add_handler(send_lucky_offer_text_command)
    app.add_handler(ban_command)
    app.add_handler(end_offer_command)
    app.add_handler(error_command)
    app.add_handler(agent_command)
    app.add_handler(worker_command)
    app.add_handler(admin_command)
    app.add_handler(start_command)
    app.add_handler(find_id_handler)
    app.add_handler(hide_ids_keyboard_handler)
    app.add_handler(back_to_user_home_page_handler)
    app.add_handler(back_to_admin_home_page_handler)

    app.add_handler(
        MessageHandler(filters=filters.ALL, callback=get_file_id),
        group=4,
    )

    # RESTART
    app.add_handler(restart_handler)

    app.add_handler(contact_dev_handler)

    app.add_error_handler(error_handler)

    app.job_queue.run_daily(
        callback=reward_worker,
        time=datetime.time(0, 0, 0),
        days=(0,),
        name="weekly_reward_worker",
        job_kwargs={
            "id": "weekly_reward_worker",
            "misfire_grace_time": None,
            "coalesce": True,
            "replace_existing": True,
        },
    )

    app.job_queue.run_daily(
        callback=reward_worker,
        time=datetime.time(0, 0),
        name="daily_reward_worker",
        job_kwargs={
            "id": "daily_reward_worker",
            "misfire_grace_time": None,
            "coalesce": True,
            "replace_existing": True,
        },
    )

    app.job_queue.run_daily(
        callback=remind_agent_to_clear_wallets,
        time=datetime.time(0, 0, tzinfo=TIMEZONE),
        name="remind_agent_to_clear_wallets",
        job_kwargs={
            "id": "remind_agent_to_clear_wallets",
            "misfire_grace_time": None,
            "coalesce": True,
            "replace_existing": True,
        },
    )

    # app.job_queue.run_daily(
    #     callback=schedule_ghafla_offer_jobs,
    #     time=datetime.time(0, 0, tzinfo=TIMEZONE),
    #     days=(1, 3, 4, 6),  # monday, wednesday, thursday, saturday
    #     name="schedule_ghafla_offer_jobs",
    #     job_kwargs={
    #         "id": "schedule_ghafla_offer_jobs",
    #         "misfire_grace_time": None,
    #         "coalesce": True,
    #         "replace_existing": True,
    #     },
    # )

    # app.job_queue.run_daily(
    #     callback=schedule_lucky_hour_jobs,
    #     time=datetime.time(0, 0, tzinfo=TIMEZONE),
    #     days=(0, 2, 4, 5),  # sunday, tuesday, thursday, friday
    #     name="schedule_lucky_hour_jobs",
    #     job_kwargs={
    #         "id": "schedule_lucky_hour_jobs",
    #         "misfire_grace_time": None,
    #         "coalesce": True,
    #         "replace_existing": True,
    #     },
    # )
    app.job_queue.run_daily(
        callback=send_daily_stats,
        time=datetime.time(23, 59, tzinfo=TIMEZONE),
        name="send_daily_stats",
        job_kwargs={
            "id": "send_daily_stats",
            "misfire_grace_time": None,
            "coalesce": True,
            "replace_existing": True,
        },
    )

    PyroClientSingleton().start()

    app.run_polling(allowed_updates=Update.ALL_TYPES, close_loop=False)

    PyroClientSingleton().stop()

    if app.bot_data["restart"]:
        os.execl(sys.executable, sys.executable, *sys.argv)
