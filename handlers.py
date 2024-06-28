from telegram import (
    Update,
)

from telegram.ext import (
    CallbackQueryHandler,
    Application,
    PicklePersistence,
    InvalidCallbackData,
    Defaults,
)

from telegram.constants import (
    ParseMode,
)

from start import (
    start_command,
    admin_command,
    worker_command,
    check_joined_handler,
    inits,
)

from jobs import (
    weekly_reward_worker,
    daily_reward_worker,
)

from common.common import (
    invalid_callback_data,
    error_handler,
    create_dot_env,
    create_folders,
    disable_httpx,
)

from common.back_to_home_page import (
    back_to_user_home_page_handler,
    back_to_admin_home_page_handler,
)

from user.withdraw import (
    withdraw_section_handler,
    withdraw_handler,
)

from user.deposit import deposit_handler
from user.buy_usdt import buy_usdt_handler
from user.make_complaint import complaint_handler
from user.user_calls import *
from user.create_account import *

from admin.admin_calls import *
from admin.admin_settings import *
from admin.wallet_settings import *
from admin.rewards_settings import *
from admin.broadcast import *
from admin.groups_settings import *
from admin.workers_settings import *

from worker.request_order import request_order_handler
from worker.check_deposit import *
from worker.process_deposit import *
from worker.check_withdraw import *
from worker.process_withdraw import *
from worker.check_buy_usdt import *
from worker.process_buy_usdt import *

from check_complaint import *

from dotenv import load_dotenv

import datetime
import os
from DB import DB


def main():
    create_dot_env()
    create_folders()
    load_dotenv()
    # disable_httpx()
    DB.creat_tables()
    defaults = Defaults(parse_mode=ParseMode.HTML)
    my_persistence = PicklePersistence(filepath="data/persistence", single_file=False)
    app = (
        Application.builder()
        .token(os.getenv("BOT_TOKEN"))
        .post_init(inits)
        # .arbitrary_callback_data(True)
        .persistence(persistence=my_persistence)
        .defaults(defaults)
        .concurrent_updates(True)
        .build()
    )

    app.add_handler(
        CallbackQueryHandler(
            callback=invalid_callback_data, pattern=InvalidCallbackData
        )
    )

    # DEPOSIT
    app.add_handler(edit_deposit_amount_handler)
    app.add_handler(add_ref_number_handler)
    app.add_handler(decline_deposit_order_handler)
    app.add_handler(check_deposit_handler)
    app.add_handler(send_order_handler)
    app.add_handler(reply_with_payment_proof_handler)
    app.add_handler(user_deposit_verified_handler)
    app.add_handler(return_deposit_order_handler)

    # WITHDRAW
    app.add_handler(check_payment_handler)
    app.add_handler(send_withdraw_order_handler)
    app.add_handler(decline_withdraw_order_handler)
    app.add_handler(return_withdraw_order_handler)
    app.add_handler(reply_with_payment_proof_withdraw_handler)
    app.add_handler(user_payment_verified_handler)

    # BUY_USDT
    app.add_handler(check_buy_usdt_handler)
    app.add_handler(send_buy_usdt_order_handler)
    app.add_handler(decline_buy_usdt_order_handler)
    app.add_handler(return_buy_usdt_order_handler)
    app.add_handler(reply_with_payment_proof_buy_usdt_handler)
    app.add_handler(user_payment_verified_buy_usdt_handler)

    # RETURN
    app.add_handler(handle_returned_buy_usdt_handler)
    app.add_handler(handle_returned_withdraw_handler)
    app.add_handler(handle_returned_deposit_handler)
    app.add_handler(reply_to_returned_complaint_handler)

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

    app.add_handler(reply_to_create_account_order_handler)
    app.add_handler(create_account_handler)
    app.add_handler(decline_create_account_handler)

    app.add_handler(withdraw_section_handler)
    app.add_handler(withdraw_handler)

    app.add_handler(buy_usdt_handler)

    app.add_handler(deposit_handler)

    app.add_handler(complaint_handler)

    # GROUPS SETTINGS
    app.add_handler(change_groups_handler)
    app.add_handler(change_group_handler)

    # ADMIN CALLS
    app.add_handler(update_usdt_to_syp_handler)
    app.add_handler(turn_user_calls_on_or_off_handler)
    app.add_handler(turn_payment_method_on_or_off_handler)
    
    app.add_handler(wallets_settings_handler)
    app.add_handler(broadcast_message_handler)

    app.add_handler(request_order_handler)

    app.add_handler(worker_settings_handler)
    app.add_handler(add_worker_cp_handler)
    app.add_handler(remove_worker_handler)
    app.add_handler(show_worker_handler)

    app.add_handler(check_joined_handler)

    app.add_handler(worker_command)
    app.add_handler(admin_command)
    app.add_handler(start_command)
    app.add_handler(find_id_handler)
    app.add_handler(hide_ids_keyboard_handler)
    app.add_handler(back_to_user_home_page_handler)
    app.add_handler(back_to_admin_home_page_handler)

    app.add_error_handler(error_handler)

    app.job_queue.run_daily(
        callback=weekly_reward_worker,
        time=datetime.time(0, 0, 0),
        days=(0,),
    )
    app.job_queue.run_daily(
        callback=daily_reward_worker,
        time=datetime.time(0, 0, 0),
    )

    app.run_polling(allowed_updates=Update.ALL_TYPES)