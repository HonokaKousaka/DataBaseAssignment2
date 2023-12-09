import json
import pymysql
import sqlite3 as sqlite
from be.model import error
from be.model import db_conn


class Seller(db_conn.DBConn):
    def __init__(self):
        db_conn.DBConn.__init__(self)

    def add_book(
        self,
        user_id: str,
        store_id: str,
        book_id: str,
        book_json_str: str,
        stock_level: int,
    ):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            if self.book_id_exist(store_id, book_id):
                return error.error_exist_book_id(book_id)
            book_info_json = json.loads(book_json_str)
            title = book_info_json.get("title")
            tags = book_info_json.get("tags")
            # 用逗号连接
            if tags is not None:
                tags = ",".join(tags)
            author = book_info_json.get("author")
            book_intro = book_info_json.get("book_intro")
            price = book_info_json.get("price")
            self.cursor = self.conn.cursor()
            # self.cursor.execute("USE DBMS;")
            self.cursor.execute(
                "INSERT into store(store_id, book_id, title, price, tags, author, book_intro, stock_level)"
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s);",
                (store_id, book_id, title, price, tags, author, book_intro, stock_level)
            )
            self.conn.commit()
        except pymysql.Error as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def add_stock_level(
        self, user_id: str, store_id: str, book_id: str, add_stock_level: int
    ):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            if not self.book_id_exist(store_id, book_id):
                return error.error_non_exist_book_id(book_id)
            self.cursor = self.conn.cursor()
            # self.cursor.execute("USE DBMS;")
            self.cursor.execute(
                "UPDATE store SET stock_level = stock_level + %s "
                "WHERE store_id = %s AND book_id = %s;",
                (add_stock_level, store_id, book_id)
            )
            self.conn.commit()
        except pymysql.Error as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def create_store(self, user_id: str, store_id: str) -> (int, str):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if self.store_id_exist(store_id):
                return error.error_exist_store_id(store_id)
            self.cursor = self.conn.cursor()
            # self.cursor.execute("USE DBMS;")
            self.cursor.execute(
                "INSERT into user_store(store_id, user_id)" "VALUES (%s, %s);",
                (store_id, user_id)
            )
            self.conn.commit()
        except pymysql.Error as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"
