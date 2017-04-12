from django import template
from interpay.models import Deposit, Withdraw, MoneyTransfer, CurrencyConversion

register = template.Library()


@register.filter
def get_transaction_type(transaction):
    if type(transaction) == Deposit:
        return "deposit"
    elif type(transaction) == Withdraw:
        return "withdraw"
    elif type(transaction) == MoneyTransfer:
        return "money_transfer"


@register.filter
def get_transfer_type(transfer, user):
    if type(transfer) == MoneyTransfer:
        if transfer.receiver.owner == user:
            return "Payment Deposit"
        elif transfer.sender.owner == user:
            return "Payment Withdraw"
    elif type(transfer) == Deposit:
        if CurrencyConversion.objects.filter(deposit=transfer):
            return "Conversion Deposit"
        else:
            return "Top Up Deposit"
    elif type(transfer) == Withdraw:
        if CurrencyConversion.objects.filter(withdraw=transfer):
            return "Conversion Withdraw"
        else:
            return "Withdraw"


@register.filter
def get_payment_sender_receiver(payment, user):
    if payment.sender.owner == user:
        return payment.receiver.owner.user.first_name + " " + payment.receiver.owner.user.last_name
    elif payment.receiver.owner == user:
        return payment.sender.owner.user.first_name + " " + payment.sender.owner.user.last_name
