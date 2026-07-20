import unittest
from account import Account, withdraw, transfer

class TestAccount(unittest.TestCase):
    def test_withdraw_rejects_overdraft(self):
        acc = Account(balance=50)
        with self.assertRaises(ValueError):
            withdraw(acc, 100)
        self.assertEqual(acc.balance, 50)

    def test_transfer_credits_destination(self):
        src = Account(balance=100)
        dst = Account(balance=0)
        transfer(src, dst, 30)
        self.assertEqual(src.balance, 70)
        self.assertEqual(dst.balance, 30)

if __name__ == "__main__":
    unittest.main()
