import sqlite3
import os
import re
import traceback
from asyncio import Lock
from constants import *

lock = Lock()


def lock_and_release(func):
    async def wrapper(*args, **kwargs):
        db = None
        cr = None
        try:
            await lock.acquire()
            db = sqlite3.connect(os.getenv("DB_PATH"))
            db.row_factory = sqlite3.Row
            cr = db.cursor()
            result = await func(*args, **kwargs, cr=cr)
            db.commit()
            if result:
                return result
        except sqlite3.Error as e:
            print(e)
            with open("errors.txt", "a", encoding="utf-8") as f:
                f.write(f"{traceback.format_exc()}\n{'-'*100}\n\n\n")
        finally:
            cr.close()
            db.close()
            lock.release()

    return wrapper


def connect_and_close(func):
    def wrapper(*args, **kwargs):
        db = sqlite3.connect(os.getenv("DB_PATH"))
        db.row_factory = sqlite3.Row
        db.create_function("REGEXP", 2, regexp)
        cr = db.cursor()
        result = func(*args, **kwargs, cr=cr)
        cr.close()
        db.close()
        return result

    return wrapper


def regexp(expr, item):
    reg = re.compile(expr)
    return reg.search(item) is not None


class DB:

    @staticmethod
    def creat_tables():
        db = sqlite3.connect(os.getenv("DB_PATH"))
        cr = db.cursor()
        script = f"""

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            name TEXT,
            deposit_balance REAL DEFAULT 0,
            gifts_balance REAL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS payment_agents (
            id INTEGER,
            name TEXT,
            username TEXT,
            method TEXT,
            approved_withdraws INTEGER DEFAULT 0,
            approved_withdraws_num INTEGER DEFAULT 0,
            approved_withdraws_day REAL DEFAULT 0,
            daily_rewards_balance REAL DEFAULT 0,
            UNIQUE(id, method) ON CONFLICT IGNORE
        );

        CREATE TABLE IF NOT EXISTS deposit_agents (
            id INTEGER PRIMARY KEY UNIQUE,
            name TEXT,
            username TEXT,
            approved_deposits REAL DEFAULT 0,
            approved_deposits_num REAL DEFAULT 0,
            approved_deposits_week REAL DEFAULT 0,
            weekly_rewards_balance REAL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS checkers (
            id INTEGER,
            name TEXT,
            username TEXT,
            check_what TEXT,
            UNIQUE(id, check_what) ON CONFLICT IGNORE

        );

        CREATE TABLE IF NOT EXISTS deposit_orders (
            serial INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            group_id INTEGER,
            checker_id INTEGER DEFAULT 0,
            worker_id INTEGER DEFAULT 0,
            state TEXT DEFAULT 'pending',
            method TEXT,
            amount REAL,
            acc_number TEXT,
            ref_number TEXT DEFAULT '',
            reason TEXT DEFAULT '',
            pending_check_message_id INTEGER,
            checking_message_id INTEGER DEFAULT 0,
            pending_process_message_id INTEGER DEFAULT 0,
            processing_message_id INTEGER DEFAULT 0,
            archive_message_ids TEXT DEFAULT '',
            complaint_took_care_of INTEGER DEFAULT 0,
            working_on_it INTEGER DEFAULT 0,
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS buyusdt_orders (
            serial INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            group_id INTEGER,
            checker_id INTEGER DEFAULT 0,
            worker_id INTEGER DEFAULT 0,
            state TEXT DEFAULT 'pending',
            method TEXT,
            amount REAL,
            bank_account_name TEXT,
            payment_method_number TEXT,
            reason TEXT DEFAULT '',
            pending_check_message_id INTEGER,
            checking_message_id INTEGER DEFAULT 0,
            pending_process_message_id INTEGER DEFAULT 0,
            processing_message_id INTEGER DEFAULT 0,
            archive_message_ids TEXT DEFAULT '',
            complaint_took_care_of INTEGER DEFAULT 0,
            working_on_it INTEGER DEFAULT 0,
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS withdraw_orders (
            serial INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            group_id INTEGER,
            checker_id INTEGER DEFAULT 0,
            worker_id INTEGER DEFAULT 0,
            state TEXT DEFAULT 'pending',
            method TEXT,
            amount REAL,
            bank_account_name TEXT,
            payment_method_number TEXT,
            acc_number TEXT,
            password TEXT,
            last_name TEXT,
            reason TEXT DEFAULT '',
            pending_check_message_id INTEGER,
            checking_message_id INTEGER DEFAULT 0, -- message in checker pm
            pending_process_message_id INTEGER DEFAULT 0,
            processing_message_id INTEGER DEFAULT 0, -- message in agent pm
            archive_message_ids TEXT DEFAULT '',
            complaint_took_care_of INTEGER DEFAULT 0,
            working_on_it INTEGER DEFAULT 0,
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS payment_methods (
            name TEXT PRIMARY KEY,
            on_off INTEGER DEFAULT 1
        );
        
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY
        );

        CREATE TABLE IF NOT EXISTS ref_numbers (
            number TEXT,
            method TEXT,
            UNIQUE(number, method) ON CONFLICT IGNORE
        );

        INSERT OR IGNORE INTO admins(id) VALUES({int(os.getenv('OWNER_ID'))});

        -- init payment methods
        INSERT OR IGNORE INTO payment_methods(name) VALUES('{USDT}');
        INSERT OR IGNORE INTO payment_methods(name) VALUES('{BEMO}');
        INSERT OR IGNORE INTO payment_methods(name) VALUES('{BARAKAH}');
        INSERT OR IGNORE INTO payment_methods(name) VALUES('{MTNCASH}');
        INSERT OR IGNORE INTO payment_methods(name) VALUES('{SYRCASH}');
        INSERT OR IGNORE INTO payment_methods(name) VALUES('{PAYEER}');
        INSERT OR IGNORE INTO payment_methods(name) VALUES('{PERFECT_MONEY}');

        """
        cr.executescript(script)

        db.commit()
        cr.close()
        db.close()


    @staticmethod
    @lock_and_release
    async def send_order(
        order_type: str,
        pending_process_message_id: int,
        serial: int,
        group_id: int,
        cr: sqlite3.Cursor = None,
    ):
        cr.execute(
            f"""
            
            UPDATE {order_type}_orders SET state = 'sent',
                                           pending_process_message_id = ?,
                                           working_on_it = 0,
                                           group_id = ?
            WHERE serial = ?
            """,
            (
                pending_process_message_id,
                group_id,
                serial,
            ),
        )

    @staticmethod
    @lock_and_release
    async def decline_order(
        order_type: str,
        archive_message_ids: int,
        reason: str,
        serial: int,
        cr: sqlite3.Cursor = None,
    ):
        cr.execute(
            f"""

            UPDATE {order_type}_orders SET state = 'declined',
                                           working_on_it = 0,
                                           reason = ?,
                                           archive_message_ids = ?
            WHERE serial = ?

            """,
            (
                reason,
                archive_message_ids,
                serial,
            ),
        )

    @staticmethod
    @lock_and_release
    async def reply_with_payment_proof(
        order_type: str,
        archive_message_ids: int,
        serial: int,
        worker_id: int,
        method: str,
        amount: float,
        cr: sqlite3.Cursor = None,
    ):
        cr.execute(
            f"""

            UPDATE {order_type}_orders SET state = 'approved',
                                           working_on_it = 0,
                                           archive_message_ids = ?
            WHERE serial = ?

            """,
            (
                archive_message_ids,
                serial,
            ),
        )

        cr.execute(
            """
            UPDATE payment_agents SET approved_withdraws = approved_withdraws + ?,
                                      approved_withdraws_day = approved_withdraws_day + ?,
                                      approved_withdraws_num = approved_withdraws_num + 1

            WHERE id = ? AND method = ?
            """,
            (amount, amount, worker_id, method),
        )

    @staticmethod
    @lock_and_release
    async def return_order(
        order_type: str,
        archive_message_ids: str,
        reason: str,
        serial: int,
        cr: sqlite3.Cursor = None,
    ):
        cr.execute(
            f"""

            UPDATE {order_type}_orders SET state = 'returned',
                                           reason = ?,
                                           working_on_it = 0,
                                           archive_message_ids = ?
            WHERE serial = ?

            """,
            (
                archive_message_ids,
                reason,
                serial,
            ),
        )

    @staticmethod
    @lock_and_release
    async def reply_with_deposit_proof(
        order_type: str,
        archive_message_ids: int,
        serial: int,
        worker_id: int,
        user_id: int,
        amount: float,
        cr: sqlite3.Cursor = None,
    ):
        cr.execute(
            f"""

            UPDATE {order_type}_orders SET state = 'approved',
                                           working_on_it = 0,
                                           archive_message_ids = ?
            WHERE serial = ?

            """,
            (
                archive_message_ids,
                serial,
            ),
        )

        cr.execute(
            """
                   UPDATE deposit_agents SET approved_deposits = approved_deposits + ?,
                                             approved_deposits_week = approved_deposits_week + ?,
                                             approved_deposits_num = approved_deposits_num + 1
                   WHERE id = ?""",
            (amount, amount, worker_id),
        )

        cr.execute(
            "UPDATE users SET deposit_balance = deposit_balance + ? WHERE id = ?",
            (amount, user_id),
        )


    @staticmethod
    @lock_and_release
    async def add_deposit_order(
        user_id: int,
        group_id: int,
        method: str,
        amount: float,
        acc_number: str,
        cr: sqlite3.Cursor = None,
    ):
        cr.execute(
            """
                INSERT OR IGNORE INTO deposit_orders(
                    user_id,
                    group_id,
                    method,
                    amount,
                    acc_number
                ) VALUES(?, ?, ?, ?, ?)
            """,
            (
                user_id,
                group_id,
                method,
                amount,
                acc_number,
            ),
        )
        cr.execute("SELECT last_insert_rowid()")

        return cr.fetchone()[0]

    @staticmethod
    @lock_and_release
    async def add_buy_usdt_order(
        user_id: int,
        group_id: int,
        method: str,
        amount: float,
        bank_account_name: str,
        payment_method_number: int,
        cr: sqlite3.Cursor = None,
    ):
        cr.execute(
            """
                INSERT OR IGNORE INTO buyusdt_orders(
                    user_id,
                    group_id,
                    method,
                    amount,
                    bank_account_name,
                    payment_method_number
                ) VALUES(?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                group_id,
                method,
                amount,
                bank_account_name,
                payment_method_number,
            ),
        )
        cr.execute("SELECT last_insert_rowid()")

        return cr.fetchone()[0]

    @staticmethod
    @lock_and_release
    async def add_withdraw_order(
        user_id: int,
        group_id: int,
        method: str,
        amount: float,
        bank_account_name: str,
        payment_method_number: int,
        acc_number: str,
        password: str,
        last_name: str,
        cr: sqlite3.Cursor = None,
    ):
        cr.execute(
            """
                INSERT OR IGNORE INTO withdraw_orders(
                    user_id,
                    group_id,
                    method,
                    amount,
                    bank_account_name,
                    payment_method_number,
                    acc_number,
                    password,
                    last_name
                ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                group_id,
                method,
                amount,
                bank_account_name,
                payment_method_number,
                acc_number,
                password,
                last_name,
            ),
        )
        cr.execute("SELECT last_insert_rowid()")

        return cr.fetchone()[0]


    @staticmethod
    @connect_and_close
    def get_checker(user_id: int, cr: sqlite3.Cursor = None):
        cr.execute("SELECT * FROM checkers WHERE id = ?", (user_id,))
        return cr.fetchall()

    @staticmethod
    @connect_and_close
    def get_payment_agent(user_id: int, cr: sqlite3.Cursor = None):
        cr.execute("SELECT * FROM payment_agents WHERE id = ?", (user_id,))
        return cr.fetchall()

    @staticmethod
    @connect_and_close
    def get_deposit_agent(user_id: int, cr: sqlite3.Cursor = None):
        cr.execute("SELECT * FROM deposit_agents WHERE id = ?", (user_id,))
        return cr.fetchone()

    @staticmethod
    @lock_and_release
    async def get_deposit_after_check_order(cr: sqlite3.Cursor = None):
        cr.execute(
            """
                SELECT * FROM deposit_orders
                WHERE working_on_it = 0 AND state = 'sent'
                LIMIT 1
            """
        )
        return cr.fetchone()

    @staticmethod
    @lock_and_release
    async def get_check_order(check_what: str, cr: sqlite3.Cursor = None):
        cr.execute(
            f"""
                SELECT * FROM {check_what}_orders
                WHERE working_on_it = 0 AND state = 'pending'
                LIMIT 1
            """
        )
        return cr.fetchone()

    @staticmethod
    @lock_and_release
    async def get_payment_order(order_type:str, method: str, cr: sqlite3.Cursor = None):
        cr.execute(
            f"""
                SELECT * FROM {order_type}_orders
                WHERE working_on_it = 0 AND method = ? AND state = 'sent'
                LIMIT 1
            """,
            (method,),
        )
        return cr.fetchone()


    @staticmethod
    @lock_and_release
    async def add_message_ids(
        serial: int,
        order_type: str,
        checking_message_id: int = 0,
        pending_check_message_id: int = 0,
        processing_message_id: int = 0,
        pending_process_message_id: int = 0,
        archive_message_ids: str = 0,
        cr: sqlite3.Cursor = None,
    ):
        table = f"{order_type}_orders"
        if archive_message_ids:
            cr.execute(
                f"UPDATE {table} SET archive_message_ids = ? WHERE serial = ?",
                (archive_message_ids, serial),
            )
        if processing_message_id:
            cr.execute(
                f"UPDATE {table} SET processing_message_id = ? WHERE serial = ?",
                (processing_message_id, serial),
            )
        if pending_process_message_id:
            cr.execute(
                f"UPDATE {table} SET pending_process_message_id = ? WHERE serial = ?",
                (pending_process_message_id, serial),
            )
        if pending_check_message_id:
            cr.execute(
                f"UPDATE {table} SET pending_check_message_id = ? WHERE serial = ?",
                (pending_check_message_id, serial),
            )
        if checking_message_id:
            cr.execute(
                f"UPDATE {table} SET checking_message_id = ? WHERE serial = ?",
                (checking_message_id, serial),
            )

    @staticmethod
    @lock_and_release
    async def add_checker_id(
        order_type: str, checker_id: int, serial: int, cr: sqlite3.Cursor = None
    ):
        cr.execute(
            f"UPDATE {order_type}_orders SET checker_id = ? WHERE serial = ?",
            (checker_id, serial),
        )

    @staticmethod
    @lock_and_release
    async def edit_order_amount(
        order_type: str, new_amount: float, serial: int, cr: sqlite3.Cursor = None
    ):
        cr.execute(
            f"UPDATE {order_type}_orders SET amount = ? WHERE serial = ?",
            (new_amount, serial),
        )

    @staticmethod
    @lock_and_release
    async def add_deposit_order_ref(
        ref_number: int, serial: int, cr: sqlite3.Cursor = None
    ):
        cr.execute(
            "UPDATE deposit_orders SET ref_number = ? WHERE serial = ?",
            (ref_number, serial),
        )

    @staticmethod
    @lock_and_release
    async def change_order_state(
        order_type: str, state: str, serial: int, cr: sqlite3.Cursor = None
    ):
        cr.execute(
            f"UPDATE {order_type}_orders SET state = ? WHERE serial = ?",
            (state, serial),
        )

    @staticmethod
    @lock_and_release
    async def add_order_reason(
        order_type: str, reason: str, serial: int, cr: sqlite3.Cursor = None
    ):
        cr.execute(
            f"UPDATE {order_type}_orders SET reason = ? WHERE serial = ?",
            (reason, serial),
        )

    @staticmethod
    @lock_and_release
    async def add_order_worker_id(
        order_type: str, worker_id: int, serial: int, cr: sqlite3.Cursor = None
    ):
        cr.execute(
            f"UPDATE {order_type}_orders SET worker_id = ? WHERE serial = ?",
            (worker_id, serial),
        )

    @staticmethod
    @lock_and_release
    async def set_working_on_it(
        order_type: str, working_on_it: int, serial: int, cr: sqlite3.Cursor = None
    ):
        cr.execute(
            f"UPDATE {order_type}_orders SET working_on_it = ? WHERE serial = ?",
            (working_on_it, serial),
        )

    @staticmethod
    @lock_and_release
    async def set_complaint_took_care_of(
        order_type: str, took_care_of: int, serial: int, cr: sqlite3.Cursor = None
    ):
        cr.execute(
            f"UPDATE {order_type}_orders SET complaint_took_care_of = ? WHERE serial = ?",
            (took_care_of, serial),
        )


    @staticmethod
    @connect_and_close
    def get_orders(order_type: str, user_id: int, cr: sqlite3.Cursor = None):
        cr.execute(f"SELECT * FROM {order_type}_orders WHERE user_id = ?", (user_id,))
        return cr.fetchall()

    @staticmethod
    @connect_and_close
    def get_one_order(order_type: str, serial: int, cr: sqlite3.Cursor = None):
        cr.execute(f"SELECT * FROM {order_type}_orders WHERE serial = ?", (serial,))
        return cr.fetchone()

    @staticmethod
    @lock_and_release
    async def add_ref_number(number: str, method: str, cr: sqlite3.Cursor = None):
        cr.execute(
            "INSERT OR IGNORE INTO ref_numbers(number, method) VALUES(?, ?)",
            (number, method),
        )

    @staticmethod
    @connect_and_close
    def get_ref_number(number: str, method: str, cr: sqlite3.Cursor = None):
        cr.execute(
            "SELECT * FROM ref_numbers WHERE number = ? AND method = ?",
            (number, method),
        )
        return cr.fetchone()

    @staticmethod
    @connect_and_close
    def get_all_workers(payments: bool = False, cr: sqlite3.Cursor = None):
        if payments:
            cr.execute("SELECT * FROM payment_agents")
        else:
            cr.execute("SELECT * FROM deposit_agents")
        return cr.fetchall()

    @staticmethod
    @connect_and_close
    def get_worker(
        worker_id: int,
        method: str = None,
        check_what: str = None,
        cr: sqlite3.Cursor = None,
    ):
        if method:
            cr.execute(
                "SELECT * FROM payment_agents WHERE id = ? AND method = ?",
                (worker_id, method),
            )
        elif check_what:
            cr.execute(
                "SELECT * FROM checkers WHERE id = ? AND check_what = ?",
                (worker_id, check_what),
            )
        else:
            cr.execute("SELECT * FROM deposit_agents WHERE id = ?", (worker_id,))
        return cr.fetchone()

    @staticmethod
    @lock_and_release
    async def weekly_reward_worker(
        worker_id: int, amount: float, cr: sqlite3.Cursor = None
    ):
        cr.execute(
            "UPDATE deposit_agents SET weekly_rewards_balance = ?, approved_deposits_week = 0 WHERE id = ?",
            (amount, worker_id),
        )

    @staticmethod
    @lock_and_release
    async def daily_reward_worker(
        worker_id: int,
        amount: float,
        method: str,
        cr: sqlite3.Cursor = None,
    ):
        cr.execute(
            "UPDATE payment_agents SET daily_rewards_balance = ?, approved_withdraws_day = 0 WHERE id = ? AND method = ?",
            (amount, worker_id, method),
        )

    @staticmethod
    @lock_and_release
    async def turn_payment_method_on_or_off(
        name: str, on: bool = False, cr: sqlite3.Cursor = None
    ):
        if on:
            cr.execute("UPDATE payment_methods SET on_off = 1 WHERE name = ?", (name,))
        else:
            cr.execute("UPDATE payment_methods SET on_off = 0 WHERE name = ?", (name,))

    @staticmethod
    @connect_and_close
    def get_payment_method(name: str, cr: sqlite3.Cursor = None):
        cr.execute("SELECT * FROM payment_methods WHERE name = ?", (name,))
        return cr.fetchone()

    @staticmethod
    @connect_and_close
    def get_payment_methods(cr: sqlite3.Cursor = None):
        cr.execute("SELECT * FROM payment_methods")
        return cr.fetchall()

    @staticmethod
    @lock_and_release
    async def add_worker(
        worker_id: int,
        name: str,
        username: str,
        method: str = None,
        check_what: str = None,
        cr: sqlite3.Cursor = None,
    ):
        if check_what:
            cr.execute(
                """
                    INSERT OR IGNORE INTO checkers(id, name, username, check_what) 
                    VALUES(?, ?, ?, ?)
                """,
                (
                    worker_id,
                    name,
                    username,
                    check_what,
                ),
            )
        elif method:
            cr.execute(
                """
                    INSERT OR IGNORE INTO payment_agents(id, name, username, method) 
                    VALUES(?, ?, ?, ?)
                """,
                (
                    worker_id,
                    name,
                    username,
                    method,
                ),
            )
        else:
            cr.execute(
                """
                    INSERT OR IGNORE INTO deposit_agents(id, name, username) 
                    VALUES(?, ?, ?)
                """,
                (
                    worker_id,
                    name,
                    username,
                ),
            )

    @staticmethod
    @connect_and_close
    def get_workers(
        method: str = None, check_what: str = None, cr: sqlite3.Cursor = None
    ):
        if method:
            cr.execute("SELECT * FROM payment_agents WHERE method = ?", (method,))
        elif check_what:
            cr.execute("SELECT * FROM checkers WHERE check_what = ?", (check_what,))
        else:
            cr.execute("SELECT * FROM deposit_agents")
        return cr.fetchall()

    @staticmethod
    @lock_and_release
    async def remove_worker(
        worker_id: int,
        method: str = None,
        check_what: str = None,
        cr: sqlite3.Cursor = None,
    ):
        if method:
            cr.execute(
                "DELETE FROM payment_agents WHERE id = ? AND method = ?",
                (worker_id, method),
            )
        elif check_what:
            cr.execute(
                "DELETE FROM checkers WHERE id = ? AND check_what = ?",
                (worker_id, check_what),
            )
        else:
            cr.execute("DELETE FROM deposit_agents WHERE id = ?", (worker_id,))

    @staticmethod
    @lock_and_release
    async def update_worker_approved_deposits(
        worder_id: int, amount: float, cr: sqlite3.Cursor = None
    ):
        cr.execute(
            """
                   UPDATE deposit_agents SET approved_deposits = approved_deposits + ?,
                                             approved_deposits_week = approved_deposits_week + ?
                   WHERE id = ?""",
            (amount, amount, worder_id),
        )

    @staticmethod
    @lock_and_release
    async def update_worker_approved_withdraws(
        worder_id: int, method: str, amount: float, cr: sqlite3.Cursor = None
    ):
        cr.execute(
            """
            UPDATE payment_agents SET approved_withdraws = approved_withdraws + ?,
                                      approved_withdraws_day = approved_withdraws_day + ?
            WHERE id = ? AND method = ?
            """,
            (amount, amount, worder_id, method),
        )

    @staticmethod
    @connect_and_close
    def check_admin(user_id: int, cr: sqlite3.Cursor = None):
        cr.execute("SELECT * FROM admins WHERE id=?", (user_id,))
        return cr.fetchone()

    @staticmethod
    @connect_and_close
    def get_admin_ids(cr: sqlite3.Cursor = None):
        cr.execute("SELECT * FROM admins")
        return cr.fetchall()

    @staticmethod
    @lock_and_release
    async def update_balance(
        user_id: int, amount: int = None, cr: sqlite3.Cursor = None
    ):
        if amount:
            cr.execute(
                "UPDATE users SET deposit_balance = deposit_balance + ? WHERE id = ?",
                (amount, user_id),
            )

    @staticmethod
    @lock_and_release
    async def update_gifts_balance(
        user_id: int, amount: int = None, cr: sqlite3.Cursor = None
    ):
        cr.execute(
            "UPDATE users SET gifts_balance = gifts_balance + ? WHERE id = ?",
            (amount, user_id),
        )
        
    @staticmethod
    @lock_and_release
    async def million_gift_user(
        user_id: int, amount: int = None, cr: sqlite3.Cursor = None
    ):
        cr.execute(
            """
                   UPDATE users SET gifts_balance = gifts_balance + ?,
                                    deposit_balance = deposit_balance - 1000000
                   WHERE id = ?""",
            (amount, user_id),
        )


    @staticmethod
    @lock_and_release
    async def add_new_user(
        user_id: int, username: str, name: str, cr: sqlite3.Cursor = None
    ):
        username = username if username else " "
        name = name if name else " "
        cr.execute(
            "INSERT INTO users(id, username, name) VALUES(?, ?, ?)",
            (user_id, username, name),
        )

    @staticmethod
    @lock_and_release
    async def add_new_admin(user_id: int, cr: sqlite3.Cursor = None):
        cr.execute("INSERT OR IGNORE INTO admins(id) VALUES(?)", (user_id,))

    @staticmethod
    @lock_and_release
    async def remove_admin(user_id: int, cr: sqlite3.Cursor = None):
        cr.execute("DELETE FROM admins WHERE id = ?", (user_id,))

    @staticmethod
    @connect_and_close
    def get_user(user_id: int, cr: sqlite3.Cursor = None):
        cr.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return cr.fetchone()

    @staticmethod
    @connect_and_close
    def get_all_users(cr: sqlite3.Cursor = None):
        cr.execute("SELECT * FROM users")
        return cr.fetchall()
