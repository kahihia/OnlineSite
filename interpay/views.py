from interpay.forms import RegistrationForm, UserForm, RechargeAccountForm, CreateBankAccountForm
from django.shortcuts import render, render_to_response, redirect
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, HttpResponse
from django.views import View
from django.views.generic import TemplateView, CreateView
from interpay.forms import RegistrationForm, UserForm
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from interpay.forms import RegistrationForm, UserForm
from django.views.decorators.csrf import csrf_exempt
from firstsite.SMS import ds, api
from interpay import models
from interpay.models import BankAccount, Deposit, Withdraw, CurrencyConversion
from random import randint
from currencies.utils import convert
from suds.client import Client
from django.contrib.auth.models import User
from interpay.models import UserProfile
import json
import time
import random
import redis
import ast
import datetime
import logging

log = logging.getLogger('interpay')


def main_page(request):
    # test()
    if request.user.is_authenticated():
        return home(request)
    return render(request, 'interpay/index.html')


def test():
    user = User.objects.get(username="arman")
    up = UserProfile.objects.get(user=user)
    ba = BankAccount(name='usdaccount', owner=up, method=BankAccount.DEBIT, cur_code='USD', account_id=make_id())
    ba.save()
    # ba = BankAccount.objects.get(owner=up, cur_code='USD')
    # ba.delete()
    d = Deposit(account=ba, amount=1000.00, banker=up, date=datetime.datetime.now(), cur_code='USD')
    d.save()


def register(request):
    registered = False
    if request.method == 'POST':
        user_form = UserForm(data=request.POST)
        registration_form = RegistrationForm(data=request.POST)

        if user_form.is_valid() and registration_form.is_valid():
            user = user_form.save()
            user.set_password(user.password)
            user.save()

            user_profile = registration_form.save(commit=False)
            user_profile.email = user_form.cleaned_data['email']
            # user_profile.date_of_birth = user_profile.cleaned_data['date_of_birth']
            user_profile.password = user.password
            user_profile.user = user

            if 'picture' in request.FILES:
                user_profile.picture = request.FILES['picture']
            if 'national_card_photo' in request.FILES:
                user_profile.national_card_photo = request.FILES['national_card_photo']
            user_profile.save()

            mobile_no = registration_form.cleaned_data['mobile_number']
            request.session['mobile_no'] = mobile_no
            request.session['username'] = user_form.cleaned_data['username']
            request.session['password'] = user_form.cleaned_data['password']
            request.session['user_id'] = models.UserProfile.objects.get(
                user__username=user_form.cleaned_data['username']).id
            registered = True
            send_sms(request, mobile_no)
        else:
            print user_form.errors, registration_form.errors

    else:
        user_form = UserForm()
        registration_form = RegistrationForm()
    activated = False
    if request.LANGUAGE_CODE == 'en-gb':
        thanks_msg = "Thank You for Registering!"
        redirect_to_home_msg = 'Launch to your homepage'
        # dict = {thanks_msg, redirect_to_home_msg}
        return render(request, 'interpay/registeration_form.html',
                      {'user_form': user_form, 'profile_form': registration_form,
                       'registered': registered,
                       'thanks_msg': thanks_msg, 'redirect_to_home_msg': redirect_to_home_msg, 'activated': activated})
    else:
        thanks_msg = "???? ?????? ??? ?? ?????? ????? ??."
        redirect_to_home_msg = '???? ???? ??? ?? ??????.'
        # dict = {thanks_msg, redirect_to_home_msg}
        return render(request, 'interpay/registeration_form.html',
                      {'user_form': user_form, 'profile_form': registration_form,
                       'registered': registered,
                       'thanks_msg': thanks_msg, 'redirect_to_home_msg': redirect_to_home_msg, 'activated': activated})


@login_required()
def trans_history(request):
    return render(request, "interpay/trans_history.html")


@csrf_exempt
def send_sms(request, mobile_no):
    # TODO : make mobile_no an optional input argument
    # mobile_no = request.session['mobile_no']
    request.session['try_counter'] = 0
    code = random_code_gen()
    # request.session['code'] = code #not needed anymore; this is checked from VerificationCodes table in database
    # redis_ds = ds.AuthCodeDataStructure()
    # redis_ds.set_code(mobile_no, code)
    #p = api.ParsGreenSmsServiceClient()
    # api.ParsGreenSmsServiceClient.sendSms(p, code=code, mobile_no=mobile_no)
    print("code:", code)
    while 1:
        try:
            user_profile = models.UserProfile.objects.get(id=request.session['user_id'])
        # do thing
        except:
            continue
        else:
            break

    # if models.VerificationCodes.objects.get(id=user_profile.id):
    #     models.VerificationCodes.objects.get(id=user_profile.id).user_code = code
    # TODO check if there exists a code for this user and replace it
    models.VerificationCodes.objects.create(user_code=code, user=user_profile)
    msg = "A code has just been sent to your phone."
    return HttpResponse(msg)


@csrf_exempt
def verify_user(request):
    request.session['try_counter'] += 1
    print request.session['try_counter']
    if request.session['try_counter'] > 3:
        html = '<div><p>Oops! you tried for 3 times.<br>Please <a href="/register/">Register again.</a></p></div>'
        result = {'res': -1, 'html': html}
        return HttpResponse(json.dumps(result))
    if request.is_ajax():
        entered_code = request.POST.get('code', False)
        # sent_code = request.session['code']
        user_prof = models.UserProfile.objects.get(id=request.session['user_id'])
        sent_code = models.VerificationCodes.objects.get(user=user_prof).user_code
        print entered_code, sent_code
        if int(entered_code) == sent_code:
            user_profile = models.UserProfile.objects.get(id=request.session['user_id'])
            user_profile.is_active = True
            user_profile.save()

            new_user = authenticate(username=request.session['username'],
                                    password=request.session['password'], )
            login(request, new_user)
            html = '<strong>Thank You for Registering!</strong><hr>' \
                   '<a class="btn-link" href="/home/">Launch to your homepage' \
                   '</a><br/>'
            result = {'res': 1, 'html': html}
            return HttpResponse(json.dumps(result))
        else:
            html = '<p style="color:red;margin-bottom:15px">The code was not correct, try again.</p>'
            result = {'res': 0, 'html': html}
            return HttpResponse(json.dumps(result))


def retrieve_pass(request):
    mobile_no = request.POST.get('mobile_no', False)
    print mobile_no
    return HttpResponse("hi")


def user_login(request):
    if request.get_full_path() == "/login/?next=/home/":
        return render(request, 'interpay/index.html', {'error': 'Your session has expired. Please log in again.'})
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)
        # user_user = models.User.objects.get(username=username)
        user_user = models.User.objects.filter(username=username)
        if not user_user:
            return render(request, "interpay/index.html", {'error': 'Username or password is invalid.'})
        else:
            user_user = user_user[0]
        user_profile = models.UserProfile.objects.get(user=user_user)

        if user:
            if user.is_active and user_profile.is_active:
                login(request, user, None)
                if request.LANGUAGE_CODE == 'en-gb':
                    return HttpResponseRedirect('/home/')
                else:
                    return HttpResponseRedirect('/fa-ir' + request.path)
            else:
                if request.LANGUAGE_CODE == 'en-gb':
                    en_acc_disabled_msg = "Your account is disabled."
                    return render(request, 'interpay/index.html', {'msg': en_acc_disabled_msg})
                else:
                    fa_acc_disabled_msg = u'???? ?????? ??? ????? ??? ???.'
                    return render(request, 'interpay/index.html', {'msg': fa_acc_disabled_msg})
        else:
            print "Invalid login details: {0}, {1}".format(username, password)
            if request.LANGUAGE_CODE == 'en-gb':
                en_wrong_info_msg = "Username or Password is not valid. please try again."
                return render(request, 'interpay/index.html', {'msg': en_wrong_info_msg})
            else:
                fa_wrong_info_msg = u'??? ?????? ?? ??? ???? ???? ??? ?????? ???.'
                return render(request, 'interpay/index.html', {'msg': fa_wrong_info_msg})
    else:
        return render(request, 'interpay/index.html', {})


START_TIME = 0x0


def make_id():
    '''
    inspired by http://instagram-engineering.tumblr.com/post/10853187575/sharding-ids-at-instagram
    '''

    t = int(time.time() * 1000) - START_TIME
    u = random.SystemRandom().getrandbits(22)
    id = (t << 22) | u
    return id


new_connection = redis.StrictRedis(host='localhost', port=6379, db=0)


@login_required()
def recharge_account(request):
    recharge_form = RechargeAccountForm(data=request.POST)
    if request.method == 'POST':
        if recharge_form.is_valid():
            cur = recharge_form.cleaned_data['currency']
            amnt = recharge_form.cleaned_data['amount']
            # print amnt, cur, request.user, request.user.id, request.user.username
            user_profile = models.UserProfile.objects.get(user=models.User.objects.get(id=request.user.id))
            # TODO : this part should be edited to check whether there is already an account with this name;
            #  if so, increment the account's total
            user_b_account, created = models.BankAccount.objects.get_or_create(
                owner=user_profile,
                cur_code=cur,
                method=models.BankAccount.DEBIT,
                name=request.user.username + '_' + cur + '_InterPay-account',
            )

            if created:
                user_b_account.account_id = make_id()
                user_b_account.save()

            banker = models.UserProfile.objects.get(user=models.User.objects.get(id=request.user.id))
            data = {"account_id": user_b_account.account_id, "amount": amnt, "banker_id": banker.id,
                    "date": str(user_b_account.when_opened), "cur_code": cur}
            new_connection.set('data', data)
            # TODO : place a logger here
            ####################################################
            zarinpal = zarinpal_payment_gate(request, amnt)
            if zarinpal['status'] == 100:
                return redirect(zarinpal['ret'])
            return HttpResponse(zarinpal['ret'])
    recharge_form = RechargeAccountForm()

    user_profile = models.UserProfile.objects.get(user=models.User.objects.get(id=request.user.id))
    deposit_set = models.Deposit.objects.filter(banker=user_profile)
    return render(request, "interpay/top_up.html", {'form': recharge_form, 'deposit_set': deposit_set})


MERCHANT_ID = 'd5dd997c-595e-11e6-b573-000c295eb8fc'
ZARINPAL_WEBSERVICE = 'https://sandbox.zarinpal.com/pg/services/WebGate/wsdl'  # real version : 'https://www.zarinpal.com/pg/services/WebGate/wsdl'
description = "this is a test"
email = 'user@user.com'
mobile = '09123456789'


def zarinpal_payment_gate(request, amount):
    call_back_url = 'http://test.rizpardakht.com/callback_handler/' + amount  # TODO : this should be changed to our website url
    client = Client(ZARINPAL_WEBSERVICE)
    result = client.service.PaymentRequest(MERCHANT_ID,
                                           amount,
                                           description,
                                           email,
                                           mobile,
                                           call_back_url)

    redirect_to = 'https://sandbox.zarinpal.com/pg/StartPay/' + str(
        result.Authority)  # the real version : 'https://www.zarinpal.com/pg/StartPay/'
    if result.Status != 100:
        redirect_to = 'Error'
    res = {'status': result.Status, 'ret': redirect_to}
    # zarinpal_callback_handler(request)
    return res


def zarinpal_callback_handler(request, amount):
    # user_profile = models.UserProfile.objects.get(id=request.user.id)
    client = Client(ZARINPAL_WEBSERVICE)

    if request.GET.get('Status') == 'OK':
        result2 = client.service.PaymentVerification(MERCHANT_ID,
                                                     request.GET.get('Authority'),
                                                     amount)
        print "result2", result2
        if result2.Status == 100:
            res = 'Transaction success. RefID: ' + str(result2.RefID)
            # TODO : place a logger here
            ##########################################
            data = new_connection.get('data')
            # print "a : ", a
            a = ast.literal_eval(data)
            new_account = models.BankAccount.objects.get(account_id=a['account_id'])
            new_banker = models.UserProfile.objects.get(id=a['banker_id'])
            deposit = models.Deposit(account=new_account, amount=a['amount'],
                                     banker=new_banker, date=a['date'], cur_code=a['cur_code'], status=True)
            deposit.save()

            # deposit_set = models.Deposit.objects.filter(banker=new_banker)
            # recharge_form = RechargeAccountForm()
            ###########################################
            #return render(request, "interpay/top_up.html", {'form': recharge_form, 'deposit_set': deposit_set, 'status': 'Success'})
            return render(request, 'interpay/test.html', {'res': res, 'result2': result2})

        elif result2.Status == 101:
            res = 'Transaction submitted : ' + str(result2.Status)
            return render(request, 'interpay/test.html', {'res': res, 'result2': result2})
        else:
            res = 'Transaction failed. Status: ' + str(result2.Status)
            return render(request, 'interpay/test.html', {'res': res, 'result2': result2})
    else:
        res = 'Transaction failed or canceled by user'
        return render(request, 'interpay/test.html', {'res': res})


# @login_required()
# def (request):
#     print 'post', request.POST
#     user_profile = models.UserProfile.objects.get(user=models.User.objects.get(id=request.user.id))
#     deposit_set = models.Deposit.objects.filter(banker=user_profile)
#     return render(request, "top_up.html", {'deposit_set': deposit_set})




@login_required()
def bank_accounts(request):
    user_profile = models.UserProfile.objects.get(user=models.User.objects.get(id=request.user.id))
    bank_account_form = CreateBankAccountForm(data=request.POST)
    if request.method == 'POST':
        print bank_account_form.errors
        if bank_account_form.is_valid():
            cur = bank_account_form.cleaned_data['cur_code']
            bank_name = bank_account_form.cleaned_data['name']
            account_no = bank_account_form.cleaned_data['account_id']
            # print bank_name, cur, request.user, request.user.id, request.user.username
            new_account = models.BankAccount(
                owner=user_profile,
                cur_code=cur,
                method=2,
                name=bank_name,
                account_id=account_no,
            )
            new_account.save()
    bank_account_form = CreateBankAccountForm()
    bank_accounts_set = models.BankAccount.objects.filter(owner=user_profile, method=2)
    return render(request, "interpay/bank_accounts.html",
                  {'bank_accounts_set': bank_accounts_set, 'form': bank_account_form})


@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect('/')


@login_required()
def home(request):
    return render(request, "interpay/home.html")


class HomeView(TemplateView):
    template_name = 'interpay/home.html'


@login_required()
def wallets(request):
    user_profile = models.UserProfile.objects.get(user=request.user)
    context = {

        'accountList': BankAccount.objects.filter(owner=user_profile),
        'user_profile': user_profile
    }
    return render(request, "interpay/wallets.html", context)


@login_required()
def wallet(request, wallet_id):
    context = {
        'account': BankAccount.objects.get(account_id=wallet_id),
    }
    return render(request, "interpay/wallet.html", context)


@login_required()
def actual_convert(request):
    amount = request.POST.get('amount')
    currency = request.POST.get('currency')
    account_id = request.POST.get('account_id')
    try:
        amount = int(amount)
    except ValueError:
        return render(request, "interpay/wallet.html",
                      {
                          'error': 'Please enter a valid number.',
                          'account': BankAccount.objects.get(account_id=account_id),
                      })
    cur_account = BankAccount.objects.get(account_id=account_id)
    user_profile = models.UserProfile.objects.get(user=request.user)
    conversion = CurrencyConversion()

    new_withdraw = Withdraw(account=cur_account, amount=amount, banker=user_profile, date=datetime.datetime.now(),
                            cur_code=cur_account.cur_code)
    new_withdraw.save()
    conversion.withdraw = new_withdraw
    converted_amount = convert(amount, cur_account.cur_code, currency)
    destination_account = ""
    for temp_account in BankAccount.objects.filter(owner=user_profile):
        if temp_account.cur_code == currency:
            destination_account = temp_account
            break
    if not destination_account:
        destination_account = BankAccount(name='usdaccount', owner=user_profile, method=BankAccount.DEBIT,
                                          cur_code=currency,
                                          account_id=make_id())
    destination_account.save()
    new_deposit = Deposit(account=destination_account, amount=converted_amount, banker=user_profile,
                          date=datetime.datetime.now(), cur_code=currency)
    new_deposit.save()
    conversion.deposit = new_deposit
    conversion.save()
    context = {
        'message': 'Your new account created successfully. Your new account id is:' + destination_account.account_id.__str__(),
        'account': BankAccount.objects.get(account_id=account_id)
    }
    return render(request, "interpay/wallet.html", context)


@login_required()
def convert_currency(request):
    from_code = request.GET.get('from_code')
    to_code = request.GET.get('to_code')
    amount = request.GET.get('amount')
    response_data = {}
    value = convert(amount, from_code, to_code)
    response_data['result'] = value.__str__()

    return HttpResponse(
        json.dumps(response_data),
        content_type="application/json"
    )


@login_required()
def reports(request):
    return render(request, "interpay/reports.html")


@login_required()
def general(request):
    return render(request, "interpay/general.html")


def random_code_gen():
    verif_code = randint(100000, 999999)
    return verif_code

# class RegistrationView(CreateView):
#     template_name = '../templates/registeration_form.html'
#     user_form = UserForm
#     registration_form = RegistrationForm
#     model = UserProfile
#     registered = False
#
#     def post(self, request, *args, **kwargs):
#         print("post called")
#         user_form = UserForm(data=request.POST)
#         registration_form = RegistrationForm(data=request.POST)
#         return self.my_form_valid(user_form)
#
#     def my_form_valid(self, user_form, request):
#         print("is valid called")
#         user = user_form.save()
#         user.set_password(user.password)
#         user.save()
#
#         user_profile = self.registration_form.save(commit=False)
#         user_profile.email = user_form.cleaned_data['email']
#         user_profile.password = user.password
#
#         if user.is_active:
#             user_profile.is_active = True
#         user_profile.user = user
#
#         if 'picture' in request.FILES:
#             user_profile.picture = request.FILES['picture']
#         user_profile.save()
#         self.registered = True
#
#         new_user = authenticate(username=user_form.cleaned_data['username'],
#                                 password=user_form.cleaned_data['password'], )
#         login(request, new_user)
#
#     def get(self):
#         user_form = UserForm()
#         registration_form = RegistrationForm()
