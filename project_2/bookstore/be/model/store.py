from datetime import datetime
import time
import logging
import os
import sqlite3 as sqlite
import pymysql
import schedule
import threading

class Store:
    database: str

    def __init__(self, db_path):
        self.database = os.path.join(db_path, "be.db")
        self.init_tables()

    def init_tables(self):
        try:
            conn = self.get_db_conn()
            cur = conn.cursor()
            cur.execute("USE DBMS;")
            cur.execute(
                "CREATE TABLE IF NOT EXISTS user ("
                "user_id VARCHAR(300) PRIMARY KEY, password VARCHAR(300) NOT NULL, "
                "balance INTEGER NOT NULL, token VARCHAR(500), terminal VARCHAR(500), "
                "INDEX index_user (user_id));"
            )

            cur.execute(
                "CREATE TABLE IF NOT EXISTS user_store ("
                "user_id VARCHAR(300), store_id VARCHAR(300) PRIMARY KEY,"
                "FOREIGN KEY (user_id) REFERENCES user(user_id),"
                "INDEX index_store (store_id))"
            )

            cur.execute(
                "CREATE TABLE IF NOT EXISTS store ("
                "store_id VARCHAR(300), book_id VARCHAR(300), title VARCHAR(100), price INTEGER, "
                "tags VARCHAR(100), author VARCHAR(100),"
                "book_intro VARCHAR(2000),stock_level INTEGER,"
                "PRIMARY KEY (store_id, book_id),"
                "FOREIGN KEY (store_id) REFERENCES user_store(store_id),"
                # 复合索引
                "INDEX index_store_book (store_id, book_id),"
                "FULLTEXT INDEX index_title(title),"
                "FULLTEXT INDEX index_tags(tags),"
                "FULLTEXT INDEX index_author(author),"
                "FULLTEXT INDEX index_book_intro(book_intro))"
            )

            cur.execute(
                "CREATE TABLE IF NOT EXISTS new_order ("
                "order_id VARCHAR(300) PRIMARY KEY , user_id VARCHAR(300), store_id VARCHAR(300), "
                "time TIMESTAMP, status INTEGER,"
                "FOREIGN KEY (user_id) REFERENCES user(user_id), "
                "FOREIGN KEY (store_id) REFERENCES user_store(store_id),"
                "INDEX index_order (order_id))"
            )

            cur.execute(
                "CREATE TABLE IF NOT EXISTS orders ("
                "order_id VARCHAR(300), book_id VARCHAR(300), count INTEGER, price INTEGER,"
                "FOREIGN KEY (order_id) REFERENCES new_order(order_id),"
                "PRIMARY KEY (order_id, book_id), "
                "INDEX index_order_book (order_id, book_id))"
            )

            conn.commit()

            def update_data():
                cur.execute("SELECT * from new_order WHERE status = 0")
                row = cur.fetchall()
                for each in row:
                    if (datetime.now() - each[3]).total_seconds() > 20:
                        cur.execute("UPDATE new_order SET status = -1 WHERE order_id = %s;", (each[0], ))
                conn.commit()

            schedule.every(1).second.do(update_data)

            def run_schedule():
                while True:
                    schedule.run_pending()
                    time.sleep(1)

            schedule_thread = threading.Thread(target=run_schedule)
            schedule_thread.start()
        except pymysql.Error as e:
            logging.error(e)
            conn.rollback()

    def get_db_conn(self):
        return pymysql.connect(
            host="127.0.0.1",
            port=3306,
            user="root",
            password="root",
            database="DBMS"
        )


database_instance: Store = None


def init_database(db_path):
    global database_instance
    database_instance = Store(db_path)


def get_db_conn():
    global database_instance
    return database_instance.get_db_conn()
