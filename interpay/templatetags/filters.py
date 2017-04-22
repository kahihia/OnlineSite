from django import template
from interpay.models import Deposit, Withdraw, MoneyTransfer, CurrencyConversion
from currencies.utils import convert
from interpay.choices import TYPE_CHOICES

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


@register.filter()
def get_is_deposit(transaction, user):
    if get_transaction_type(transaction) == "deposit":
        return True
    if get_transfer_type(transaction, user) == "Payment Deposit":
        return True
    if get_transfer_type(transaction, user) == "Conversion Deposit":
        return True
    if get_transfer_type(transaction, user) == "Top Up Deposit":
        return True
    return False


@register.filter()
def get_is_withdraw(transaction, user):
    if get_transaction_type(transaction) == "withdraw":
        return True
    if get_transfer_type(transaction, user) == "Payment Withdraw":
        return True
    if get_transfer_type(transaction, user) == "Conversion Withdraw":
        return True
    return False


@register.filter()
def get_currency(cur_code):
    if cur_code == "EUR":
        return "Euro"
    if cur_code == "USD":
        return "Dollar"
    if cur_code == "IRR":
        return "Rial"


@register.filter()
def withdraw_convert_currency(amount, source_currency):
    return convert(amount, source_currency, 'IRR')


@register.filter()
def get_type(transaction_type):
    if transaction_type:
        return TYPE_CHOICES[int(transaction_type)][1]
    else:
        return 'Payment'
