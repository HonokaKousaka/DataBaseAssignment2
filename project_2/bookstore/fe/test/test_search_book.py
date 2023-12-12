import pytest
from fe.access.new_buyer import register_new_buyer
from fe.test.gen_book_data import GenBook
import uuid


class TestSearchBook:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        self.seller_id = "test_new_order_seller_id_{}".format(str(uuid.uuid1()))
        self.store_id = "test_new_order_store_id_{}".format(str(uuid.uuid1()))
        self.buyer_id = "test_new_order_buyer_id_{}".format(str(uuid.uuid1()))
        self.password = self.seller_id
        self.buyer = register_new_buyer(self.buyer_id, self.password)
        self.gen_book = GenBook(self.seller_id, self.store_id)
        yield

    def test_ok(self):
        ok, method, info = self.gen_book.gen_book_info()
        assert ok
        
        code = self.buyer.search_book("title", "test")
        assert code == 200

    def test_ok_store(self):
        ok, method, info = self.gen_book.gen_book_info()
        assert ok
        
        code = self.buyer.search_book("title", "test", self.store_id)
        assert code == 200

    def test_not_exist_store(self):
        ok, method, info = self.gen_book.gen_book_info()
        assert ok
        
        self.store_id = self.store_id + "_x"
        code = self.buyer.search_book("title", "test", self.store_id)
        assert code != 200