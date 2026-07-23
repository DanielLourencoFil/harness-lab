class Account:
    def __init__(self, balance=0):
        self.balance = balance

def withdraw(acc, amount):
    acc.balance -= amount

def transfer(src, dst, amount):
    withdraw(src, amount)
    src.balance += amount
