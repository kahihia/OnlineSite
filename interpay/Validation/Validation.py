class Validation:
    def __init__(self):
        print ("init")

    @staticmethod
    def check_validation(error_code):
        if error_code == "non_positive":
            return "Entered Number should be greater than zero."
        if error_code == "invalid_amount":
            return "Please enter a valid number for amount."
        if error_code == "insufficient_balance":
            return "Your balance is not sufficient."
