In account.py there are 2 bugs: withdraw() allows the balance to go negative
(it should raise ValueError if amount > balance), and transfer() credits the
wrong account (it should credit dst, not src). Fix ONLY account.py so that
`python3 -m unittest test_account.py -v` passes. Do not edit test_account.py.
