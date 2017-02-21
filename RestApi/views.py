from interpay.models import UserProfile, BankAccount, Deposit
from rest_framework import viewsets
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from django.http import HttpResponse
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from interpay.views import make_id
import datetime
import json
from django.utils import timezone

class JSONResponse(HttpResponse):
    """
    An HttpResponse that renders its content into JSON.
    """

    def __init__(self, data, **kwargs):
        content = JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)


def generate_token(request):
    user = User.objects.get(username='arman')
    # token = Token.objects.create(user=user)
    token = Token.objects.get(user=user)
    print(token.key)
    return HttpResponse(token.key)


def check_validation(code):
    return code


def get_status_message(code):
    if code == 1:
        return "success"
    elif code == 2:
        return "Invalid email or mobile number."
    elif code == 3:
        return "No user with specified information."


@api_view(['GET', 'POST'])
def get_order_status(request):
    response = {}
    if request.method == "POST":
        data = JSONParser().parse(request)
        merchant_order_reference = data['MerOrderRef']
        order_reference = data['orderReference']
        # merchant_order = MerchantOrder.objects.filter(number = merchant_order_reference)
        # deposit = merchant_order.deposit
        deposit = ""
        try:
            deposit = Deposit.objects.get(id=order_reference)
        except:
            response['status_code'] = -2
            response['status_message'] = "Invalid order reference number."
            return JSONResponse(response)
        if deposit:
            response['status_code'] = int(deposit.status)
            if deposit.status == 1:
                response['status_message'] = "reversal"
            elif deposit.status == 2:
                response['status_message'] = "pending"
            elif deposit.status == 3:
                response['status_message'] = "settled"
            response['order_reference'] = deposit.id
            response['merOrderRef'] = merchant_order_reference
            response['orderAmount'] = deposit.amount
            response['totalAmount'] = deposit.amount
            response['orderDate'] = deposit.date
            response['expiryDate'] = deposit.date + datetime.timedelta(days=7)
            response['status'] = 1
            return JSONResponse(response)


@api_view(['GET', 'POST'])
def cash_out_order(request):
    response = {}
    if request.method == "POST":
        data = JSONParser().parse(request)
        payee_email = data['payeeEmail']
        payee_mobile = data['payeeMobile']
        order_amount = data['orderAmount']
        merchant_order_reference = data['MerOrderRef']
        currency = data['orderCurrencyCode']
        response['orderAmount'] = order_amount
        response['totalAmount'] = order_amount
        response['merOrderRef'] = merchant_order_reference
        response['statusCode'] = check_validation(1)
        response['statusMessage'] = get_status_message(1)
        if UserProfile.objects.filter(email=payee_email) or UserProfile.objects.filter(mobile_number=payee_mobile):
            user = UserProfile.objects.get(email=payee_email)
            if not user:
                user = UserProfile.objects.get(mobile_number=payee_mobile)
                response['statusCode'] = check_validation(2)
                response['statusMessage'] = get_status_message(2)
                return JSONResponse(response)
            else:
                if str(user.mobile_number) == str(payee_mobile):

                    bank_account = BankAccount.objects.filter(owner=user, cur_code=currency)
                    if bank_account:
                        bank_account = bank_account[0]
                    else:
                        bank_account = BankAccount.objects.create(owner=user, method=BankAccount.DEBIT,
                                                                  cur_code=currency,
                                                                  account_id=make_id())
                    deposit = Deposit.objects.create(account=bank_account, amount=order_amount, status=Deposit.PENDING)
                    response['orderReference'] = deposit.id
                    response['orderDate'] = datetime.datetime.now()
                    response['expiryDate'] = response['orderDate'] + datetime.timedelta(days=7)
                    response['status'] = "pending"
                    return JSONResponse(response)
                else:
                    if UserProfile.objects.filter(email=payee_email) or UserProfile.objects.filter(
                            mobile_number=payee_mobile):
                        response['statusCode'] = check_validation(2)
                        response['statusMessage'] = get_status_message(2)
                        return JSONResponse(response)
        else:
            response['statusCode'] = check_validation(3)
            response['statusMessage'] = get_status_message(3)
            return JSONResponse(response)
    return HttpResponse('None.')


@api_view(['GET', 'POST'])
def cash_out_reversal(request):
    response = {}
    if request.method == "POST":
        data = JSONParser().parse(request)
        order_reference = data['orderReference']
        merchant_order_reference = data['MerOrderRef']
        deposit = ""
        try:
            deposit = Deposit.objects.get(id=order_reference)
        except:
            response['statusCode'] = -2
            response['statusMessage'] = "Invalid order reference number."
            return JSONResponse(response)
        if deposit:
            if deposit.status == Deposit.COMPLETED:
                response['statusCode'] = -3
                response['statusMessage'] = "Transaction was unsuccessful. Money has been withdrawn."
                return JSONResponse(response)
            deposit.status = Deposit.REVERSED
            deposit.save()
            # merchant_order = MerchantOrder.objects.filter(number=merchant_order_reference)
            # deposit = merchant_order.deposit
            response['statusCode'] = deposit.status
            response['statusMessage'] = get_status_message(deposit.status)
            response['orderReference'] = order_reference
            response['merOrderRef'] = merchant_order_reference
            response['orderAmount'] = deposit.amount
            response['totalAmount'] = deposit.amount
            response['orderDate'] = deposit.date
            response['expiryDate'] = deposit.date + datetime.timedelta(days=7)
            response['status'] = 1
            return JSONResponse(response)


@api_view(['GET', 'POST'])
def get_pending_orders(request):
    response = {}
    if request.method == "POST":
        data = JSONParser().parse(request)
        page = data['page']
        size = data['size']
        sort = data['sort']
        deposit = ""
        orders = []
        if (page - 1) * size >= Deposit.objects.filter(status=Deposit.PENDING).__len__():
            response['statusCode'] = -4
            response['statusMessage'] = "There is no request in specified range."
            return JSONResponse(response)
        for order in Deposit.objects.filter(status=Deposit.PENDING)[(page - 1) * size:]:
            current_order = {
                'orderReference': order.id,
                'merOrderRef': 1,
                'orderAmount': order.amount,
                'totalAmount': order.amount,
                'orderDate': str(order.date),
                'expiryDate': str(order.date + datetime.timedelta(days=7)),
                'status': "Pending"
            }
            orders.append(current_order)
            if orders.__len__() == size:
                break
        response['orders'] = json.dumps(orders)
        response['statusCode'] = 1
        response['statusMessage'] = "Success"
        response['numberOfElements'] = orders.__len__()
        return JSONResponse(response)
    return HttpResponse('None.')


@api_view(['GET', 'POST'])
def get_paid_orders(request):
    response = {}
    if request.method == "POST":
        data = JSONParser().parse(request)
        page = data['page']
        size = data['size']
        sort = data['sort']
        deposit = ""
        orders = []
        if (page - 1) * size >= Deposit.objects.filter(status=Deposit.COMPLETED).__len__():
            response['statusCode'] = -4
            response['statusMessage'] = "There is no request in specified range."
            return JSONResponse(response)
        for order in Deposit.objects.filter(status=Deposit.COMPLETED)[(page - 1) * size:]:
            current_order = {
                'orderReference': order.id,
                'merOrderRef': 1,
                'orderAmount': order.amount,
                'totalAmount': order.amount,
                'orderDate': str(order.date),
                'expiryDate': str(order.date + datetime.timedelta(days=7)),
                'status': "Completed"
            }
            orders.append(current_order)
        response['orders'] = json.dumps(orders)
        # merchant_order = MerchantOrder.objects.filter(number=merchant_order_reference)
        # deposit = merchant_order.deposit
        response['statusCode'] = 1
        response['statusMessage'] = "Success"
        return JSONResponse(response)
    return HttpResponse('None.')


@api_view(['GET', 'POST'])
def get_expired_orders(request):
    response = {}
    if request.method == "POST":
        data = JSONParser().parse(request)
        page = data['page']
        size = data['size']
        sort = data['sort']
        deposit = ""
        orders = []
        if (page - 1) * size >= Deposit.objects.filter(status=Deposit.PENDING).__len__():
            response['statusCode'] = -4
            response['statusMessage'] = "There is no request in specified range."
            return JSONResponse(response)
        for order in Deposit.objects.filter(status=Deposit.PENDING)[(page - 1) * size:]:
            if order.date + datetime.timedelta(days=7) < timezone.now():
                current_order = {
                    'orderReference': order.id,
                    'merOrderRef': 1,
                    'orderAmount': order.amount,
                    'totalAmount': order.amount,
                    'orderDate': str(order.date),
                    'expiryDate': str(order.date + datetime.timedelta(days=7)),
                    'status': "Pending"
                }
                orders.append(current_order)
        response['orders'] = json.dumps(orders)
        # merchant_order = MerchantOrder.objects.filter(number=merchant_order_reference)
        # deposit = merchant_order.deposit
        response['statusCode'] = 1
        response['statusMessage'] = "Success"
        return JSONResponse(response)
    return HttpResponse('None.')
