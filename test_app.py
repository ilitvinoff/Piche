import unittest
from app import app
import accounts

class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        # Reset in-memory storage before each test
        accounts.accounts_by_name.clear()
        accounts.accounts.clear()
        accounts.next_account_id = 1

    def create_account(self, name="alice", password="pass", balance=100.0):
        return self.client.post(
            "/create_account",
            json={"name": name, "password": password, "balance": balance}
        )

    def login(self, name="alice", password="pass"):
        return self.client.post(
            "/login",
            json={"name": name, "password": password}
        )

    def get_auth_header(self, name="alice", password="pass"):
        resp = self.login(name, password)
        token = resp.get_json().get("access_token")
        return {"Authorization": f"Bearer {token}"}

    def test_create_account_success(self):
        resp = self.create_account()
        self.assertEqual(resp.status_code, 201)
        data = resp.get_json()
        self.assertIn("id", data)
        self.assertEqual(data["name"], "alice")
        self.assertNotIn("password", data)

    def test_create_account_duplicate(self):
        self.create_account()
        resp = self.create_account()
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.get_json())

    def test_create_account_invalid_data(self):
        resp = self.client.post("/create_account", json={"name": "", "password": "", "balance": -1})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.get_json())

    def test_login_success(self):
        self.create_account()
        resp = self.login()
        self.assertEqual(resp.status_code, 200)
        self.assertIn("access_token", resp.get_json())

    def test_login_failure(self):
        resp = self.login()
        self.assertEqual(resp.status_code, 401)
        self.assertIn("error", resp.get_json())

    def test_deposit_success(self):
        self.create_account()
        headers = self.get_auth_header()
        resp = self.client.post("/deposit", json={"account_id": 1, "amount": 50}, headers=headers)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["balance"], 150.0)

    def test_deposit_invalid_token(self):
        self.create_account()
        resp = self.client.post("/deposit", json={"account_id": 1, "amount": 50})
        self.assertEqual(resp.status_code, 401)

    def test_deposit_invalid_data(self):
        self.create_account()
        headers = self.get_auth_header()
        resp = self.client.post("/deposit", json={"account_id": 1, "amount": -10}, headers=headers)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.get_json())

    def test_deposit_account_not_found(self):
        self.create_account()
        headers = self.get_auth_header()
        resp = self.client.post("/deposit", json={"account_id": 999, "amount": 10}, headers=headers)
        self.assertEqual(resp.status_code, 404)
        self.assertIn("error", resp.get_json())

    def test_withdraw_success(self):
        self.create_account()
        headers = self.get_auth_header()
        resp = self.client.post("/withdraw", json={"account_id": 1, "amount": 50}, headers=headers)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["balance"], 50.0)

    def test_withdraw_insufficient_funds(self):
        self.create_account()
        headers = self.get_auth_header()
        resp = self.client.post("/withdraw", json={"account_id": 1, "amount": 200}, headers=headers)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.get_json())

    def test_withdraw_invalid_token(self):
        self.create_account()
        resp = self.client.post("/withdraw", json={"account_id": 1, "amount": 10})
        self.assertEqual(resp.status_code, 401)

    def test_withdraw_invalid_data(self):
        self.create_account()
        headers = self.get_auth_header()
        resp = self.client.post("/withdraw", json={"account_id": 1, "amount": -10}, headers=headers)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.get_json())

    def test_transfer_success(self):
        self.create_account(name="alice", password="pass", balance=100)
        self.create_account(name="bob", password="word", balance=50)
        headers = self.get_auth_header("alice", "pass")
        resp = self.client.post("/transfer", json={
            "from_account_id": 1, "to_account_id": 2, "amount": 30
        }, headers=headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data[0]["balance"], 70.0)
        self.assertEqual(data[1]["balance"], 80.0)

    def test_transfer_insufficient_funds(self):
        self.create_account(name="alice", password="pass", balance=10)
        self.create_account(name="bob", password="word", balance=50)
        headers = self.get_auth_header("alice", "pass")
        resp = self.client.post("/transfer", json={
            "from_account_id": 1, "to_account_id": 2, "amount": 30
        }, headers=headers)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.get_json())

    def test_transfer_same_account(self):
        self.create_account(name="alice", password="pass", balance=100)
        headers = self.get_auth_header("alice", "pass")
        resp = self.client.post("/transfer", json={
            "from_account_id": 1, "to_account_id": 1, "amount": 10
        }, headers=headers)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.get_json())

    def test_transfer_invalid_token(self):
        self.create_account(name="alice", password="pass", balance=100)
        self.create_account(name="bob", password="word", balance=50)
        resp = self.client.post("/transfer", json={
            "from_account_id": 1, "to_account_id": 2, "amount": 10
        })
        self.assertEqual(resp.status_code, 401)

    def test_transfer_invalid_data(self):
        self.create_account(name="alice", password="pass", balance=100)
        self.create_account(name="bob", password="word", balance=50)
        headers = self.get_auth_header("alice", "pass")
        resp = self.client.post("/transfer", json={
            "from_account_id": 1, "to_account_id": 2, "amount": -10
        }, headers=headers)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.get_json())

    def test_unexpected_error(self):
        from unittest.mock import patch
        def side_effect(*a, **kw): raise Exception("fail!")

        self.create_account()
        headers = self.get_auth_header()
        with patch("app.deposit", side_effect=side_effect):
            resp = self.client.post("/deposit", json={"account_id": 1, "amount": 10}, headers=headers)
            self.assertEqual(resp.status_code, 500)
            self.assertIn("error", resp.get_json())

if __name__ == "__main__":
    unittest.main()