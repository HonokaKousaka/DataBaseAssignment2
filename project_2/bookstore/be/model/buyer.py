import pymysql
from datetime import datetime
import sqlite3 as sqlite
import uuid
import json
import logging
from be.model import db_conn
from be.model import error


class Buyer(db_conn.DBConn):
    def __init__(self):
        db_conn.DBConn.__init__(self)

    def new_order(
        self, user_id: str, store_id: str, id_and_count: [(str, int)]
    ) -> (int, str, str):
        order_id = ""
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + (order_id,)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id) + (order_id,)
            uid = "{}_{}_{}".format(user_id, store_id, str(uuid.uuid1()))

            self.cursor = self.conn.cursor()
            # self.cursor.execute("USE DBMS;")
            self.cursor.execute(
                "INSERT INTO new_order(order_id, user_id, store_id, time, status) "
                "VALUES(%s, %s, %s, %s, %s);",
                (uid, user_id, store_id, datetime.now(), 0)
            )
            for book_id, count in id_and_count:
                self.cursor.execute(
                    "SELECT book_id, stock_level, price FROM store "
                    "WHERE store_id = %s AND book_id = %s;",
                    (store_id, book_id)
                )
                row = self.cursor.fetchone()
                if row is None:
                    return error.error_non_exist_book_id(book_id) + (order_id,)

                stock_level = row[1]
                price = row[2]

                if stock_level < count:
                    return error.error_stock_level_low(book_id) + (order_id,)

                self.cursor.execute(
                    "UPDATE store set stock_level = stock_level - %s "
                    "WHERE store_id = %s and book_id = %s and stock_level >= %s; ",
                    (count, store_id, book_id, count)
                )
                if self.cursor.rowcount == 0:
                    return error.error_stock_level_low(book_id) + (order_id,)

                self.cursor.execute(
                    "INSERT INTO orders(order_id, book_id, count, price) "
                    "VALUES(%s, %s, %s, %s);",
                    (uid, book_id, count, price)
                )
            self.conn.commit()

            order_id = uid
        except pymysql.Error as e:
            logging.info("528, {}".format(str(e)))
            return 528, "{}".format(str(e)), ""
        except BaseException as e:
            logging.info("530, {}".format(str(e)))
            return 530, "{}".format(str(e)), ""

        return 200, "ok", order_id

    def payment(self, user_id: str, password: str, order_id: str) -> (int, str):
        conn = self.conn
        self.cursor = conn.cursor()
        try:
            # self.cursor.execute("USE DBMS;")
            self.cursor.execute(
                "SELECT user_id, store_id FROM new_order WHERE order_id = %s AND status = %s;",
                (order_id, 0)
            )
            row = self.cursor.fetchone()
            if row is None:
                return error.error_invalid_order_id(order_id)

            buyer_id = row[0]
            store_id = row[1]

            if buyer_id != user_id:
                return error.error_authorization_fail()

            self.cursor.execute(
                "SELECT balance, password FROM user WHERE user_id = %s;", (buyer_id,)
            )
            row = self.cursor.fetchone()
            if row is None:
                return error.error_non_exist_user_id(buyer_id)
            balance = row[0]
            if password != row[1]:
                return error.error_authorization_fail()

            self.cursor.execute(
                "SELECT store_id, user_id FROM user_store WHERE store_id = %s;",
                (store_id,)
            )
            row = self.cursor.fetchone()
            if row is None:
                return error.error_non_exist_store_id(store_id)

            seller_id = row[1]

            if not self.user_id_exist(seller_id):
                return error.error_non_exist_user_id(seller_id)

            self.cursor.execute(
                "SELECT count, price FROM orders WHERE order_id = %s;",
                (order_id,)
            )
            total_price = 0
            # results = self.cursor.fetchall()
            for row in self.cursor:
                count = row[0]
                price = row[1]
                total_price = total_price + price * count

            if balance < total_price:
                return error.error_not_sufficient_funds(order_id)

            self.cursor.execute(
                "UPDATE user set balance = balance - %s WHERE user_id = %s AND balance >= %s;",
                (total_price, buyer_id, total_price)
            )
            if self.cursor.rowcount == 0:
                return error.error_not_sufficient_funds(order_id)

            self.cursor.execute(
                "UPDATE user set balance = balance + %s WHERE user_id = %s;",
                (total_price, seller_id)
            )

            if self.cursor.rowcount == 0:
                return error.error_non_exist_user_id(buyer_id)

            self.cursor.execute(
                "UPDATE new_order SET status = %s where order_id = %s;", (1, order_id)
            )

            conn.commit()

        except pymysql.Error as e:
            return 528, "{}".format(str(e))

        except BaseException as e:
            return 530, "{}".format(str(e))

        return 200, "ok"

    def add_funds(self, user_id, password, add_value) -> (int, str):
        try:
            self.cursor = self.conn.cursor()
            # self.cursor.execute("USE DBMS;")
            self.cursor.execute(
                "SELECT password from user where user_id=%s;", (user_id,)
            )
            row = self.cursor.fetchone()
            if row is None:
                return error.error_authorization_fail()

            if row[0] != password:
                return error.error_authorization_fail()

            self.cursor.execute(
                "UPDATE user SET balance = balance + %s WHERE user_id = %s;",
                (add_value, user_id),
            )
            if self.cursor.rowcount == 0:
                return error.error_non_exist_user_id(user_id)
            self.conn.commit()
        except pymysql.Error as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))

        return 200, "ok"

    # 确认收货操作
    def receive_order(self, user_id, password, order_id) -> (int, str):
        try: 
            self.cursor = self.conn.cursor()
            self.cursor.execute(
                "SELECT password from user where user_id=%s;", (user_id,)
            )
            row = self.cursor.fetchone()
            if row is None:
                return error.error_authorization_fail()

            if row[0] != password:
                return error.error_authorization_fail()
            
            self.cursor.execute(
                "SELECT user_id, status from new_order where order_id = %s;", (order_id, )
            )
            row = self.cursor.fetchone()
            if row is None:
                return error.error_invalid_order_id(order_id)
            
            status = row[1]

            if status == -1:
                return error.error_invalid_order_id(order_id)
            elif status == 0:
                return error.error_order_not_paid(order_id)
            elif status == 1:
                return error.error_order_not_delivered(order_id)
            
            self.cursor.execute("UPDATE new_order SET status = %s where order_id = %s;",
                                (3, order_id))
            self.conn.commit()
        except pymysql.Error as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))

        return 200, "ok"

    # 搜索图书
    def search_book(self, keywords, method: str = 'title', store_id: str = None) -> (int, str):
        available_method = ['title', 'tags', 'author', 'book_intro']
        if method not in available_method:
            return error.error_invalid_search_method(method)
        
        if store_id is not None and not self.store_id_exist(store_id):
            return error.error_non_exist_store_id
        
        # like是模糊查找
        search = "SELECT book_id FROM store where %s like %s;"
        if store_id is not None:
            search = "SELECT book_id FROM store where %s like %s AND store_id = %s;"
        
        try:
            self.cursor = self.conn.cursor()
            if store_id is not None:
                self.cursor.execute(search, (method, keywords, store_id))
            else:
                self.cursor.execute(search, (method, keywords))
        except pymysql.Error as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))

        return 200, "ok"

    # 搜索订单
    def search_order(self, user_id: str, password: str) -> (int, str):
        try:
            self.cursor = self.conn.cursor()
            self.cursor.execute("SELECT password FROM user where user_id = %s;", (user_id, ))
            row = self.cursor.fetchone()

            if row is None:
                return error.error_non_exist_user_id(user_id)

            if not password == row[0]:
                return error.error_authorization_fail()

            self.cursor.execute("SELECT * FROM new_order LEFT JOIN orders ON new_order.order_id = orders.order_id "
                                "WHERE new_order.user_id = %s;", (user_id, ))
        except pymysql.Error as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))

        return 200, "ok"

    # 取消订单
    def cancel_order(self, user_id, password, order_id) -> (int, str):
        try:
            self.cursor = self.conn.cursor()
            self.cursor.execute("SELECT password FROM user WHERE user_id = %s;", (user_id, ))
            row = self.cursor.fetchone()

            if row is None:
                return error.error_non_exist_user_id(user_id)

            if not password == row[0]:
                return error.error_authorization_fail()

            self.cursor.execute("SELECT user_id, status, store_id FROM new_order WHERE order_id = %s;", (order_id, ))
            row = self.cursor.fetchone()
            if row is None:
                return error.error_invalid_order_id(order_id)

            status = row[1]
            store_id = row[2]

            if status == -1:
                return error.error_invalid_order_id(order_id)
            elif status == 2:
                return error.error_order_delivered(order_id)
            elif status == 3:
                return error.error_order_was_received(order_id)
            
            self.cursor.execute()
        except pymysql.Error as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))

        return 200, "ok"