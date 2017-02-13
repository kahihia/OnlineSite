from interpay.models import UserProfile, BankAccount, Deposit
from rest_framework import viewsets
from RestApi.serializers import UserSerializer, GroupSerializer
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


class JSONResponse(HttpResponse):
    """
    An HttpResponse that renders its content into JSON.
    """

    def __init__(self, data, **kwargs):
        content = JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)


@api_view(['GET', 'POST'])
def snippet_list(request):
    """
    List all snippets, or create a new snippet.
    """
    if request.method == 'GET':
        users = UserProfile.objects.all()
        serializer = UserSerializer(users, many=True, context={'request': request})
        return JSONResponse(serializer.data)

    elif request.method == 'POST':
        data = JSONParser().parse(request)
        user = UserSerializer(data=data)
        if user.is_valid():
            user.save()
            return JSONResponse(user.data, status=status.HTTP_201_CREATED)
        return Response(user.errors, status=status.HTTP_400_BAD_REQUEST)


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
        print (payee_mobile)
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
                        bank_account = BankAccount.objects.create(owner=user, method=BankAccount.DEBIT, cur_code=currency,
                                                                  account_id=make_id())
                    deposit = Deposit.objects.create(account=bank_account, amount=order_amount, status=Deposit.PENDING)
                    response['orderReference'] = deposit.id
                    response['orderDate'] = datetime.datetime.now()
                    response['expiryDate'] = response['orderDate'] + datetime.timedelta(days=7)
                    response['status'] = 1
                    return JSONResponse(response)

                else:
                    if UserProfile.objects.filter(email=payee_email) or UserProfile.objects.filter(mobile_number=payee_mobile):
                        response['statusCode']=check_validation(2)
                        response['statusMessage'] = get_status_message(2)
                        return JSONResponse(response)
    # print (request.POST['Authorization'])
    #     app_id = request.POST.get('appId', False)
    #     # app_key = request.POST.get('appKey',None)
    #     # order_type = request.POST.get['orderType']
    #     # payee_name = request.POST['payeeName']
    #     payee_email = request.POST.get('payeeEmail', False)
    #     payee_email = request.POST['payeeEmail']
    #     # payee_mobile = request.POST['payeeMobile']
    #     # customer_name = request.POST['customerName']
    #     # customer_email = request.POST['customerEmail']
    #     # customer_mobile = request.POST['customerMobile']
    #     # customer_address_line1 = request.POST['customerAddressLine1']
    #     # customer_address_line2 = request.POST['customerAddressLine2']
    #     # order_currency_code = request.POST['orderCurrencyCode']
    #     # order_amount = request.POST['orderAmount']
    #     print (payee_email)
    #     if UserProfile.objects.filter(email=payee_email):
    #         print ('user exists')
    #     return HttpResponse('done')
    # else:
    return HttpResponse('None.')
