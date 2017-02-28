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
from interpay.forms import RegistrationForm, UserForm, CaptchaForm
from django.views.decorators.csrf import csrf_exempt
from firstsite.SMS import ds, api
from interpay import models
from smtplib import SMTPRecipientsRefused
from interpay.models import BankAccount, Deposit, Withdraw, CurrencyConversion, WithdrawalRequest
from random import randint
from currencies.utils import convert
from suds.client import Client
from django.contrib.auth.models import User
from interpay.models import UserProfile, MoneyTransfer
from django.core.mail import send_mail
from interpay.Email import Email
# from django.conf import settings
from firstsite import settings
import json
import time
import random
import redis
import ast
import datetime
import logging
import requests

log = logging.getLogger('interpay')


def main_page(request):
    # test()
    if (models.Rule.objects.count() == 0):
        log.debug('1Initialising comission because no Rule objects exists')
        r = models.Rule(start_date=datetime.datetime.now().date(),
                        end_date=(datetime.datetime.now() + datetime.timedelta(days=100)).date())
        r.save()
        r = models.Rule(start_date=datetime.datetime.now().date(), cur_code='IRR',
                        end_date=(datetime.datetime.now() + datetime.timedelta(days=100)).date())
        r.save()
    if request.user.is_authenticated():
        return home(request)
    return render(request, 'interpay/index.html')


def test():
    user = User.objects.get(username="arman")
    up = UserProfile.objects.get(user=user)
    ba = BankAccount(name='usdaccount', owner=up, method=BankAccount.DEBIT, cur_code='IRR', account_id=make_id())
    ba.save()
    # ba = BankAccount.objects.get(owner=up, cur_code='USD')
    # ba.delete()
    d = Deposit(account=ba, amount=1000.00, banker=up, date=datetime.datetime.now(), cur_code='IRR')
    d.save()


def register(request):
    print ("test")
    registered = False
    if request.method == 'POST':
        print ("pooost")
        user_form = UserForm(data=request.POST)
        registration_form = RegistrationForm(data=request.POST)

        # gcapcha = request.POST['g-recaptcha-response']
        # post_data = {'secret': '6LfHKRMUAAAAAJG-cEV-SPcophf8jyXvrcghDtur', 'response': gcapcha}
        # response = requests.post('https://www.google.com/recaptcha/api/siteverify', data=post_data)
        # content = response.json()
        # if not content['success']:
        #     return render(request, "interpay/registeration_form.html", {'error': 'Captcha is not entered.'})

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
            # note that request.session['user_id'] variable refers to userProfile id
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
    p = api.ParsGreenSmsServiceClient()
    api.ParsGreenSmsServiceClient.sendSms(p, code, mobile_no, request.session['user_id'])
    print("code:", code)
    user_profile = ''
    while 1:
        try:
            user_profile = models.UserProfile.objects.get(id=request.session['user_id'])
        # do thing
        except:
            # user_profile = models.UserProfile.objects.get(id=request.user.id)
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
    global new_connection
    new_connection = settings.connect_to_redis()
    request.session['try_counter'] += 1
    print request.session['try_counter']
    if request.session['try_counter'] > 3:
        html = '<div><p>Oops! you tried for 3 times.<br>Please <a href="/register/">Register again.</a></p></div>'
        new_connection.delete(request.session['user_id'])
        print "user code with id = ", request.session['user_id'], " deleted"
        result = {'res': -1, 'html': html}
        return HttpResponse(json.dumps(result))
    if request.is_ajax():
        entered_code = request.POST.get('code', False)
        # sent_code = request.session['code']
        user_prof = models.UserProfile.objects.get(id=request.session['user_id'])
        sent_code = models.VerificationCodes.objects.get(user=user_prof).user_code
        print entered_code, sent_code
        # TODO: check if the expire time of the sent code has passed; so the condition
        # is not satisfied even if the entered code is correct
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


@login_required()
def pay_user(request):
    if request.method == "POST":
        up = ""
        currency = request.POST['currency']
        amount = request.POST['amount']
        comment = request.POST['comment']
        if not comment:
            comment = ""
        if not amount:
            return render(request, 'interpay/pay_user.html', {'error': 'Please enter amount.'})
        if not amount.isdigit():
            return render(request, 'interpay/pay_user.html', {'error': 'Please enter a valid number for amount.'})
        if int(amount) <= 0:
            return render(request, 'interpay/pay_user.html',
                          {'error': 'Please enter a number greater than zero for amount.'})
        email = request.POST['email']
        mobile = request.POST['mobile']
        # if not email and not mobile:
        #     return render(request, 'interpay/pay_user.html', {'error': 'Please enter destination email or mobile.'})
        if email:
            up = UserProfile.objects.filter(email=email)
            if up:
                up = up[0]
            else:
                return render(request, 'interpay/pay_user.html', {'error': 'No user with this email.'})
        elif mobile:
            up = UserProfile.objects.filter(mobile=mobile)
            if up:
                up = up[0]
            else:
                return render(request, 'interpay/pay_user.html', {'error': 'No user with this mobile number.'})
        else:
            return render(request, 'interpay/pay_user.html', {'error': 'Please enter destination email or mobile.'})
        destination_account = ""
        if up:
            user_debit_accounts = BankAccount.objects.filter(owner=up, method=BankAccount.DEBIT)
            for account in user_debit_accounts:
                if account.cur_code == currency:
                    destination_account = account
                    break
        src_account_owner = UserProfile.objects.filter(user=request.user)
        if src_account_owner:
            src_account_owner = src_account_owner[0]
        src_account = BankAccount.objects.filter(owner=src_account_owner, method=BankAccount.DEBIT, cur_code=currency)
        if src_account:
            src_account = src_account[0]
            # d = Deposit(account=src_account, amount=1000.00, banker=UserProfile.objects.get(user=request.user), date=datetime.datetime.now(), cur_code='USD')
            # d.save()
            if src_account.balance < int(amount):
                return render(request, 'interpay/pay_user.html', {'error': 'Your balance is less than entered amount.'})
            if destination_account:
                MoneyTransfer.objects.create(sender=src_account, receiver=destination_account,
                                             date=datetime.datetime.now(),
                                             amount=amount, comment=comment, cur_code=currency)
                return render(request, "interpay/pay_user.html", {'success': 'Your payment was successfully done.'})
            else:
                return render(request, 'interpay/pay_user.html',
                              {'error': 'No destination account with this currency.'})
        else:
            return render(request, 'interpay/pay_user.html',
                          {'error': 'You do not have any account in this currency. '})
    return render(request, "interpay/pay_user.html")


def reset_password(request, token):
    global new_connection
    new_connection = settings.connect_to_redis()
    if request.method == "POST":
        birth_date = request.POST['birth_date']
        national_id = request.POST['national_id']
        mobile_number = request.POST['mobile_number']
        new_password = request.POST['new_password']
        re_new_password = request.POST['re_new_password']
        user_id = request.POST['user']
        print ('user: ', str(birth_date))
        if new_password != re_new_password:
            return render(request, 'interpay/reset_password.html', {
                'error': 'Both fields must match. '
            })
        user = User.objects.get(id=int(user_id))
        user_profile = UserProfile.objects.get(user=user)
        if user_profile.mobile_number != mobile_number:
            return render(request, 'interpay/reset_password.html', {
                'error': 'mobile number is not valid.'
            })
        if user_profile.national_code != national_id:
            return render(request, 'interpay/reset_password.html', {
                'error': 'national id is not valid.'
            })
        if str(user_profile.date_of_birth.date()) != str(birth_date):
            return render(request, 'interpay/reset_password.html', {
                'error': 'date of birth is not valid.'
            })

        user.set_password(new_password)
        user.save()
        return render(request, 'interpay/reset_password.html', {
            'success': 'Your password successfully changed. '
        })

    if request.method == "GET":
        data = new_connection.get(token)
        data = ast.literal_eval(data)
        user = User.objects.get(id=int(data['user_id']))
        return render(request, 'interpay/reset_password.html', {'user': user})


def retrieve_pass(request):
    email = request.POST.get('email', False)
    email_sender = Email.Email(email)
    error_message = ""
    sent = ""
    try:
        sent = email_sender.send_email()

    except SMTPRecipientsRefused:
        error_message = "Invalid Email"
    if sent == 1:
        return HttpResponse("Password retrieved successful")
    else:
        if error_message:
            return HttpResponse(error_message)
        return HttpResponse("No such user")


def activate_account(request, token):
    global new_connection
    new_connection = settings.connect_to_redis()
    if request.method == 'POST':
        birth_date = request.POST['birth_date']
        national_id = request.POST['national_id']
        mobile_number = request.POST['mobile_number']
        new_password = request.POST['new_password']
        re_new_password = request.POST['re_new_password']
        user_id = request.POST['user']
        user = User.objects.get(id=user_id)
        up = UserProfile.objects.get(user=user)
        up.date_of_birth = birth_date
        up.national_code = national_id
        up.mobile_number = mobile_number
        up.is_active = True
        up.save()
        if new_password != re_new_password:
            return render(request, 'interpay/reset_password.html', {
                'error': 'Both fields must match. '
            })
        user.set_password(new_password)
        user.save()
        return render(request, 'interpay/index.html')
    if request.method == "GET":
        data = new_connection.get(token)
        data = ast.literal_eval(data)
        user = User.objects.get(id=int(data['user_id']))
        return render(request, 'interpay/activate_account.html', {'user': user})
        # return render(request, 'interpay/activate_account.html')


def user_login(request):
    if request.get_full_path() == "/login/?next=/home/":
        return render(request, 'interpay/index.html',
                      {'error': 'Your session has expired. Please log in again.', 'captcha_form': CaptchaForm()})
    if request.method == 'POST':
        print ("user login")
        username = request.POST['username']
        password = request.POST['password']
        print (settings.DEBUG, "debug")
        if not settings.DEBUG:
            gcapcha = request.POST['g-recaptcha-response']
            # post  https://www.google.com/recaptcha/api/siteverify
            post_data = {'secret': '6LfHKRMUAAAAAJG-cEV-SPcophf8jyXvrcghDtur', 'response': gcapcha}
            response = requests.post('https://www.google.com/recaptcha/api/siteverify', data=post_data)
            content = response.json()

            if not content['success']:
                return render(request, "interpay/index.html", {'error': 'Captcha is not entered.'})
        user = authenticate(username=username, password=password)

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


# new_connection = redis.StrictRedis(host='localhost', port=6379, db=0,password='interpass')
new_connection = settings.connection


@login_required()
def recharge_account(request, **message):
    global new_connection
    new_connection = settings.connect_to_redis()
    code = 0
    msg_color = 0
    if message:
        emessage = message['message']
        msg_color = 1
    else:
        emessage = ''

    recharge_form = RechargeAccountForm(data=request.POST)
    if request.method == 'POST':
        if recharge_form.is_valid():
            cur = recharge_form.cleaned_data['currency']
            amnt = recharge_form.cleaned_data['amount']
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
                    "date": str(datetime.datetime.utcnow()), "cur_code": cur}

            log.debug("new BankAccount object created and saved")
            zarinpal = zarinpal_payment_gate(request, amnt)
            new_connection.set(zarinpal['Authority'], data)  # TODO: set proper TTL
            print data, "cached in redis"
            log.debug("Connected to redis")
            code = zarinpal['status']
            print code
            if code == 100:
                log.debug("redirecting to " + zarinpal['ret'])
                return redirect(zarinpal['ret'])
    recharge_form = RechargeAccountForm()
    try:

        user_profile = models.UserProfile.objects.get(user=models.User.objects.get(id=request.user.id))
        deposit_set = models.Deposit.objects.filter(banker=user_profile)

    except Exception as e:
        log.debug('an exception occurred : ', e)
        deposit_set = models.Deposit.none()
    if code == -3:
        emessage = "Entered value too small. This payment will not accept less than 100."
    else:
        if code != 0:
            emessage = "Unknown ZarinPal Error"
    print msg_color, "msg_color"
    return render(request, "interpay/top_up.html",
                  {'form': recharge_form, 'deposit_set': deposit_set, 'code': code, 'emessage': emessage,
                   'msg_color': msg_color})


MERCHANT_ID = 'd5dd997c-595e-11e6-b573-000c295eb8fc'
ZARINPAL_WEBSERVICE = 'https://sandbox.zarinpal.com/pg/services/WebGate/wsdl'  # real version : 'https://www.zarinpal.com/pg/services/WebGate/wsdl'
description = "this is a test"
email = 'user@user.com'
mobile = '09123456789'


def zarinpal_payment_gate(request, amount):
    call_back_url = 'http://127.0.0.1:8000/callback_handler/' + amount  # TODO : this should be changed to our website url
    client = Client(ZARINPAL_WEBSERVICE)
    result = client.service.PaymentRequest(MERCHANT_ID,
                                           amount,
                                           description,
                                           email,
                                           mobile,
                                           call_back_url)
    log.debug("called zarinpal payment request")

    redirect_to = 'https://sandbox.zarinpal.com/pg/StartPay/' + str(
        result.Authority)  # the real version : 'https://www.zarinpal.com/pg/StartPay/'

    res = {'Authority': result.Authority, 'status': result.Status, 'ret': redirect_to}
    return res


def zarinpal_callback_handler(request, amount):
    client = Client(ZARINPAL_WEBSERVICE)
    if request.GET.get('Status') == 'OK':
        auth = request.GET.get('Authority')
        result2 = client.service.PaymentVerification(MERCHANT_ID,
                                                     auth,
                                                     amount)
        print "result2", result2
        if result2.Status == 100:
            res = 'Transaction success. RefID: ' + str(result2.RefID)
            log.debug("new Deposit object created and saved")
            data = new_connection.get(auth)
            a = ast.literal_eval(data)
            new_account = models.BankAccount.objects.get(account_id=a['account_id'])
            new_banker = models.UserProfile.objects.get(id=a['banker_id'])
            deposit = models.Deposit(account=new_account, amount=float(a['amount']),
                                     banker=new_banker,
                                     date=(datetime.datetime.strptime(a['date'].__str__()[:10], '%Y-%m-%d')),
                                     cur_code=a['cur_code'],
                                     tracking_code=result2.RefID)
            # try:
            deposit.calculate_comission()  # automatically saves after calculating comission
            # except:
            #     log.error("error in Calculating Comission")
            #     deposit.save()

            # return render(request, 'interpay/test.html', {'res': res, 'result2': result2})
            return recharge_account(request, message="Your account charged successfully.")

        elif result2.Status == 101:
            res = 'Transaction submitted : ' + str(result2.Status)
            # return render(request, 'interpay/test.html', {'res': res, 'result2': result2})
            return recharge_account(request, message="Your transaction has been successfully submitted earlier.")
        else:
            res = 'Transaction failed. Status: ' + str(result2.Status)
            # return render(request, 'interpay/test.html', {'res': res, 'result2': result2})
            return recharge_account(request, message="Your transaction was not successful. Try again later.")
    else:
        res = 'Transaction failed or canceled by user'
        # return render(request, 'interpay/test.html', {'res': res})
        return recharge_account(request, message="Transaction failed or canceled by you.")


@login_required()
def bank_accounts(request):
    user_profile = models.UserProfile.objects.get(user=models.User.objects.get(id=request.user.id))
    mymessage = ''
    bank_account_form = CreateBankAccountForm(data=request.POST)
    if request.method == 'POST':
        if bank_account_form.is_valid():
            cur = bank_account_form.cleaned_data['cur_code']
            bank_name = bank_account_form.cleaned_data['name']
            account_no = bank_account_form.cleaned_data['account_id']
            # print bank_name, cur, request.user, request.user.id, request.user.username

            new_account, created = models.BankAccount.objects.get_or_create(
                owner=user_profile,
                cur_code=cur,
                name=bank_name,
                account_id=account_no,
                method=models.BankAccount.WITHDRAW,
            )

            if not created:
                mymessage = account_no
                mymessage += ": Error, that account has already been added."

            new_account.save()
        else:
            if request.POST['account_id']:
                account = BankAccount.objects.filter(account_id=request.POST['account_id'])
                amount = request.POST['amount']
                account_id = request.POST['account_id']
                if account:
                    account = account[0]
                    debit_accounts = BankAccount.objects.filter(owner=account.owner, method=1)
                    if not debit_accounts:
                        bank_account_form = CreateBankAccountForm()
                        bank_accounts_set = models.BankAccount.objects.filter(owner=user_profile,
                                                                              method=BankAccount.WITHDRAW)
                        return render(request, 'interpay/bank_accounts.html',
                                      {'error': 'No debit account.', 'bank_accounts_set': bank_accounts_set,
                                       'form': bank_account_form, 'emessage': mymessage})

                    bank_account_form = CreateBankAccountForm()
                    bank_accounts_set = models.BankAccount.objects.filter(owner=user_profile,
                                                                          method=BankAccount.WITHDRAW)

                    src_account = debit_accounts[0]
                    if src_account.balance < amount:
                        print ('error')
                        return render(request, 'interpay/bank_accounts.html', {'bank_accounts_set': bank_accounts_set,
                                                                               'form': bank_account_form,
                                                                               'emessage': mymessage,
                                                                               'error': 'Your balance is less than requested amount.',
                                                                               'account_id': account_id})
                    withdraw_request = WithdrawalRequest(src_account=src_account, dest_account=account, amount=amount)
                    withdraw_request.save()
                    return render(request, 'interpay/bank_accounts.html', {'bank_accounts_set': bank_accounts_set,
                                                                           'form': bank_account_form,
                                                                           'emessage': mymessage,
                                                                           'success_message': 'Your request successfully saved.',
                                                                           'account_id': account_id})
                    # for other_account in BankAccount.objects.filter(owner=account.owner, method='Debit')

    bank_account_form = CreateBankAccountForm()
    bank_accounts_set = models.BankAccount.objects.filter(owner=user_profile, method=BankAccount.WITHDRAW) \
        .order_by('name')
    return render(request, "interpay/bank_accounts.html",
                  {'bank_accounts_set': bank_accounts_set, 'form': bank_account_form, 'emessage': mymessage})


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

        'accountList': BankAccount.objects.filter(owner=user_profile, method=BankAccount.DEBIT),
        'user_profile': user_profile
    }
    return render(request, "interpay/wallets.html", context)


@login_required()
def wallet(request, wallet_id, recom=None):
    # print "wallet function"
    ba = BankAccount.objects.get(account_id=wallet_id, method=BankAccount.DEBIT)
    # print recom

    if request.method == "GET":
        recom = request.GET.get("recom")
    print recom
    if recom == None:
        context = {
            'account': ba,
            'recommended': 0,
            'deposit_set': models.Deposit.objects.filter(account=ba),
        }
    else:
        context = {
            'account': ba,
            'recommended': ba.balance,
            'deposit_set': models.Deposit.objects.filter(account=ba),
        }

    return render(request, "interpay/wallet.html", context)


@login_required()
def wallet_recommended(request, wallet_id):
    context = {
        'account': BankAccount.objects.get(account_id=wallet_id, method=BankAccount.DEBIT),
        'recommended': BankAccount.objects.get(account_id=wallet_id, method=BankAccount.DEBIT).balance,
        'deposit_set': models.Deposit.objects.filter(banker=wallet_id),
    }
    return render(request, "interpay/wallet.html", context)


@login_required()
def withdraw_pending_deposit(request):
    if request.method == 'POST':
        print ('entered post')
        deposit_id = request.POST.get('deposit_id')
        deposit = Deposit.objects.get(id=deposit_id)
        deposit.status = Deposit.COMPLETED
        deposit.save()
        account = deposit.account

        context = {
            'account_id': account.id,
            'transaction_status': 'Requested amount was withdrawn successfully.',
            'account': account,
            'deposit_set': Deposit.objects.filter(account=account),
            'deposit_id': deposit.id,
            'withdraw_set': Withdraw.objects.filter(account=account),
        }

        return render(request, 'interpay/wallet.html', context)
    return HttpResponseRedirect('../')

@login_required()
def actual_convert(request):
    if request.method == 'POST':
        amount = request.POST.get('amount')
        currency = request.POST.get('currency')
        account_id = request.POST.get('account_id')
        try:
            amount = float(amount)
        except ValueError:
            return render(request, "interpay/wallet.html",
                          {
                              'error': 'Please enter a valid number.',
                              'account': BankAccount.objects.get(account_id=account_id),
                          })
        if amount <= 0:
            return render(request, "interpay/wallet.html",
                          {
                              'error': 'Entered Number should be greater that zero.',
                              'account': BankAccount.objects.get(account_id=account_id),
                          })
        cur_account = BankAccount.objects.get(account_id=account_id)

        if cur_account.balance < amount:
            return render(request, "interpay/wallet.html",
                          {
                              'error': 'Your balance is not sufficient.',
                              'account': BankAccount.objects.get(account_id=account_id),
                          })
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
            destination_account = BankAccount(name='wall_account', owner=user_profile, method=BankAccount.DEBIT,
                                              cur_code=currency,
                                              account_id=make_id())
        destination_account.save()
        new_deposit = Deposit(account=destination_account, amount=float(converted_amount), banker=user_profile,
                              date=datetime.datetime.now(), cur_code=currency)
        new_deposit.calculate_comission()
        new_deposit.save()
        conversion.deposit = new_deposit
        conversion.save()
        context = {
            'account_id': destination_account.account_id.__str__(),
            'message': 'Your new account created successfully. Your new account id is:' + destination_account.account_id.__str__(),
            'account': BankAccount.objects.get(account_id=account_id),
            'deposit_set': models.Deposit.objects.filter(account=cur_account),
        }
        return render(request, "interpay/wallet.html", context)
    else:
        return render(request, "interpay/wallet.html",
                      {
                          'error': 'Invalid GET Request. Contact Admin',
                      })


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
