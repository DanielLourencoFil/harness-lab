class Account:
    def __init__(self, balance=0):
        self.balance = balance

def withdraw(acc, amount):
    if amount > acc.balance:
        raise ValueError("insufficient funds")
    acc.balance -= amount

def transfer(src, dst, amount):
    withdraw(src, amount)
    dst.balance += amount
