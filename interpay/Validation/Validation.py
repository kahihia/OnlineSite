import sys
class Validation:
    NEGATIVE=1
    VALUE_ERROR=2
    INSUFFICIENT_BALANCE=3
    OK=10
    choices = {NEGATIVE: 'Entered number should be greater than zero.', VALUE_ERROR: 'Please enter a valid number for amount.', INSUFFICIENT_BALANCE: "Your balance is not sufficient." }

    def __init__(self):
        print ("init validation")


    def check_value(self, amount, balance=sys.maxsize):
        try:
            amount = float(amount)
        except ValueError:
            return self.VALUE_ERROR
        if balance <= int(amount):
           self.INSUFFICIENT_BALANCE
        if int(amount) <= 0:
            return self.NEGATIVE
        return self.OK

    def get_errormessage(self, v):
        return self.choices.get(v, 'unknown error')
    @staticmethod
    def check_validation(error_code):
        if error_code == "non_positive":
            return "Entered Number should be greater than zero."
        if error_code == "invalid_amount":
            return "Please enter a valid number for amount."
        if error_code == "insufficient_balance":
            return "Your balance is not sufficient."
