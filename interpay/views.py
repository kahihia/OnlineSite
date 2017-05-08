import os

from django.core.files.base import ContentFile


from interpay.forms import RegistrationForm, UserForm, RechargeAccountForm, CreateBankAccountForm
from django.shortcuts import render, render_to_response, redirect
# from groupcache.decorators import cache_tagged_page
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.vary import vary_on_headers
from django.http import HttpResponseRedirect, HttpResponse
from django.utils.cache import get_cache_key
from django.views import View
from django.views.generic import TemplateView, CreateView
from interpay.forms import RegistrationForm, UserForm
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from interpay.forms import RegistrationForm, UserForm, CaptchaForm
from django.views.decorators.csrf import csrf_exempt
from interpay.Validation import Validation
from firstsite.SMS import ds, api
from interpay import models
from smtplib import SMTPRecipientsRefused
from interpay.models import BankAccount, Deposit, Withdraw, CurrencyConversion, WithdrawalRequest, CurrencyReserve, Review
from random import randint
from currencies.utils import convert
from suds.client import Client
from django.contrib.auth.models import User
from interpay.models import UserProfile, MoneyTransfer
from interpay.Email import Email
from firstsite import settings
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from currencies.models import Currency
from django.db import transaction
from django.db.models import Q
import json
import time
import random
import redis
import ast
import datetime
import logging
import requests
import BeautifulSoup
import xml.sax
from django.utils.translation import ugettext_lazy as _
from Notification.views import NotificationClass
from Notification.models import Notification
from django.utils import timezone
from jdatetime import GregorianToJalali

from django.core.mail import send_mail
from django.views.generic.base import RedirectView

log = logging.getLogger('interpay')


# @every(seconds=10)

def get_currency_rate(currency):
    response = requests.get('http://kajex.com/')
    soup = BeautifulSoup.BeautifulSoup(response.content)
    table = soup.findAll("table", {"id": "arz_table"})[0]
    x = 0
    buy_price = ""
    sell_price = ""
    for td in table.findAll('td'):
        if td.string == currency:
            x += 1
            continue
        if x == 1:
            buy_price = td.contents[0]
            x += 1
            continue
        if x == 2:
            sell_price = td.contents[0]
            break
    try:
        sell_price = int(sell_price)
        buy_price = int(buy_price)
    except:
        return HttpResponse("An error was occured.")

    main_price = (sell_price + buy_price) / 2
    return main_price


def set_notification_seen(request):
    if request.method == "GET":
        notif_id = request.GET["notif_id"]
        notification = Notification.objects.get(id=notif_id)
        notification.seen = True
        notification.save()
    return


def set_rates(request):
    if not request.user.is_authenticated() or not request.user.is_superuser:
        return HttpResponse("Error")

    euro_rate = get_currency_rate("EUR")
    dollar_rate = get_currency_rate("USD")

    dollar_to_euro_ratio = float(dollar_rate) / (euro_rate * 1.00)
    dollar_to_euro_ratio = float("{0:.2f}".format(dollar_to_euro_ratio))
    dollar = Currency.objects.get(code='USD')
    dollar.factor = dollar_to_euro_ratio
    dollar.save()

    rial = Currency.objects.get(code='IRR')
    rial.factor = euro_rate
    rial.save()
    return HttpResponse("Successful")


# @cache_page(20)
# def cache_test(request):
#     print ("entered cache test")
#     return HttpResponse(2 * 4 + 6)
#
#
# def cache_write(request):
#     cache.set('my_key', 'test message', 20)
#     return HttpResponse("write")
#
#
# def cache_read(request):
#     return HttpResponse(cache.get('my_key'))
def get_currency(cur_code):
    if cur_code == "EUR":
        return "Euro"
    if cur_code == "USD":
        return "Dollar"
    if cur_code == "IRR":
        return "Rial"


def main_page(request):
    # test()
    if (models.Rule.objects.count() == 0):
        log.debug('Initialising comission because no Rule objects exists')
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
    print ("test executed")
    user = User.objects.get(username="arman")
    up = UserProfile.objects.get(user=user)
    # ba = BankAccount(name='usdaccount', owner=up, method=BankAccount.DEBIT, cur_code='IRR', account_id=make_id())
    # ba.save()
    ba = BankAccount.objects.filter(owner=up, method=BankAccount.DEBIT, cur_code='IRR')[0]
    # ba.delete()
    d = Deposit(account=ba, amount=1000.00, banker=up, date=datetime.datetime.now(), cur_code='IRR')
    d.save()


def register(request):
    registered = False
    if request.method == 'POST':
        user_form = UserForm(data=request.POST)
        registration_form = RegistrationForm(data=request.POST)
        if not settings.DEBUG:
            gcapcha = request.POST['g-recaptcha-response']
            # post  https://www.google.com/recaptcha/api/siteverify
            post_data = {'secret': '6LfHKRMUAAAAAJG-cEV-SPcophf8jyXvrcghDtur', 'response': gcapcha}
            response = requests.post('https://www.google.com/recaptcha/api/siteverify', data=post_data)
            content = response.json()
            if not content['success']:
                return render(request, "interpay/registeration_form.html",
                              {'error': _("Captcha is not entered."), 'user_form': user_form,
                               'profile_form': registration_form, })

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
        thanks_msg = _("Thank You for Registering!")
        redirect_to_home_msg = _("Launch to your homepageee")
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
def edit(request):
    return render(request, "interpay/edit.html")


@login_required()
def transaction_history(request):
    user_bank_accounts = BankAccount.objects.filter(owner__user=request.user, method=BankAccount.DEBIT)
    up = UserProfile.objects.get(user=request.user)
    transaction_list = []
    for item in user_bank_accounts:
        for item1 in Deposit.objects.filter(account=item):
            transaction_list.append(item1)
        for item2 in Withdraw.objects.filter(account=item):
            transaction_list.append(item2)
            # for item3 in MoneyTransfer.objects.filter(Q(receiver__owner=up) | Q(sender__owner=up)).filter(
            #                 Q(receiver=item) | Q(sender=item)):
            #     transaction_list.append(item3)
    transaction_list.sort(key=lambda x: x.date, reverse=True)
    if request.LANGUAGE_CODE == 'fa-ir':
        for transaction in transaction_list:
            cur_date = timezone.localtime(transaction.date)
            jalali_date_obj = GregorianToJalali(cur_date.year, cur_date.month, cur_date.day)
            year, month, day = jalali_date_obj.getJalaliList()
            transaction.date = str(year) + "-" + str(month) + "-" + str(day) + ", " + str(cur_date.hour) + ":" + str(
                cur_date.minute) + ":" + str(cur_date.second)

    context = {
        'transaction_list': transaction_list,
        'user': up,
    }
    return render(request, "interpay/trans_history.html", context)


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
    msg = _("A code has just been sent to your phone.")
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


@transaction.atomic()
@login_required()
def pay_user(request):
    if request.LANGUAGE_CODE == 'en-gb':
        langStr = ""
    else:
        langStr = '/' + request.LANGUAGE_CODE

    if request.method == "POST":
        up = ""
        currency = request.POST['currency']
        amount = request.POST['amount']
        comment = request.POST['comment']
        email = request.POST['email']
        mobile = request.POST['mobile']
        setform = request.POST.get('setform', False)

        context_error_amount = {
            'currency': currency,
            'amount': amount,
            'comment': comment,
            'email': email,
            'mobile': mobile,
            'setform': setform,
            'error': "Please enter amount."
        }

        if not comment:
            comment = ""
        if not amount:
            return render(request, 'interpay/pay_user.html', context_error_amount)

        v = Validation.Validation()
        er = v.check_value(amount)
        context_error_validation = {
            'currency': currency,
            'amount': amount,
            'comment': comment,
            'email': email,
            'mobile': mobile,
            'setform': setform,
            'error': v.get_errormessage(er),
            'langStr': langStr
        }
        if not er == Validation.Validation.OK:
            return render(request, "interpay/pay_user.html",context_error_validation)



        # if not email and not mobile:
        #     return render(request, 'interpay/pay_user.html', {'error': 'Please enter destination email or mobile.'})
        context_error_email = {
            'currency': currency,
            'amount': amount,
            'comment': comment,
            'email': email,
            'mobile': mobile,
            'setform': setform,
            'error': _("No user with this email.")
        }
        if email:
            up = UserProfile.objects.filter(email=email)
            if up:
                up = up[0]
            else:
                return render(request, 'interpay/pay_user.html', context_error_email)
        elif mobile:
            up = UserProfile.objects.filter(mobile=mobile)
            if up:
                up = up[0]
            else:
                context_error_mobile = {
                    'currency': currency,
                    'amount': amount,
                    'comment': comment,
                    'email': email,
                    'mobile': mobile,
                    'setform': setform,
                    'error': _("No user with this mobile number.")
                }
                return render(request, 'interpay/pay_user.html', context_error_mobile)
        else:
            context_error_mobile_email = {
                'currency': currency,
                'amount': amount,
                'comment': comment,
                'email': email,
                'mobile': mobile,
                'setform': setform,
                'error': _("Please enter destination email or mobile.")
            }
            return render(request, 'interpay/pay_user.html', context_error_mobile_email)

        if(up.user==request.user):
            context_error_pay_yourself = {
                'currency': currency,
                'amount': amount,
                'comment': comment,
                'email': email,
                'mobile': mobile,
                'setform': setform,
                'error': _("You cannot send payment to yourself")
            }
            return render(request, 'interpay/pay_user.html',context_error_pay_yourself)

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
            if src_account.balance < int(amount):
                context_error_balance = {
                    'currency': currency,
                    'amount': amount,
                    'comment': comment,
                    'email': email,
                    'mobile': mobile,
                    'setform': setform,
                    'error': Validation.Validation.check_validation('insufficient_balance')
                }
                return render(request, 'interpay/pay_user.html', context_error_balance)
            if not destination_account:
                destination_account = BankAccount.objects.create(name = currency + '_InterPay-account',owner=up, cur_code=currency, method=BankAccount.DEBIT,
                                                                 account_id=make_id())
            withdraw = Withdraw.objects.create(banker=src_account_owner, account=src_account, amount=amount, cur_code=src_account.cur_code,
                                               type=Withdraw.PAYMENT)
            deposit = Deposit.objects.create(banker=up, account=destination_account, amount=amount,
                                             cur_code=destination_account.cur_code, type=Deposit.PAYMENT)
            MoneyTransfer.objects.create(deposit=deposit, withdraw=withdraw, comment=comment)
            NotificationClass.make_notification(
                "You have a new payment from" + src_account_owner.user.first_name + " " + src_account_owner.user.last_name + ". You have received " + amount + " " + get_currency(
                    deposit.cur_code) + "s.", up,
                                                '/wallets/' + str(destination_account.account_id))
            return render(request, "interpay/pay_user.html",
                          {'success': _("Your payment was successfully done"), 'langStr': langStr})
        else:
            context_error_currency = {
                'currency': currency,
                'amount': amount,
                'comment': comment,
                'email': email,
                'mobile': mobile,
                'setform': setform,
                'error': _("You do not have any account in this currency")
            }
            return render(request, 'interpay/pay_user.html', context_error_currency)
    return render(request, "interpay/pay_user.html", {'langStr': langStr})


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
                'error': _("Both fields must match.")
            })
        user = User.objects.get(id=int(user_id))
        user_profile = UserProfile.objects.get(user=user)
        if user_profile.mobile_number != mobile_number:
            return render(request, 'interpay/reset_password.html', {
                'error': _("mobile number is not valid.")
            })
        if user_profile.national_code != national_id:
            return render(request, 'interpay/reset_password.html', {
                'error': _("national id is not valid.")
            })
        if str(user_profile.date_of_birth.date()) != str(birth_date):
            return render(request, 'interpay/reset_password.html', {
                'error': _("date of birth is not valid.")
            })

        user.set_password(new_password)
        user.save()
        return render(request, 'interpay/reset_password.html', {
            'success': _("Your password successfully changed.")
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
        return HttpResponse(_("Password retrieved successful"))
    else:
        if error_message:
            return HttpResponse(error_message)
        return HttpResponse(_("No such user"))


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
                'error': _("Both fields must match.")
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
    if request.method == 'GET':
        next = request.GET.get("next")
        if not next:
            next = "/home/"
    if request.get_full_path() == "/login/?next=/home/":
        log.info("logging user out")
        user_logout(request)
        # return render(request, 'interpay/index.html',
                   #   {'error': 'Your session has expired. Please log in again.', 'captcha_form': CaptchaForm()})
    if request.method == 'POST':
        next = request.POST.get("next")
        if not next:
            next = "/home/"
        username = request.POST['username']
        password = request.POST['password']
        if not settings.DEBUG:
            gcapcha = request.POST['g-recaptcha-response']
            # post  https://www.google.com/recaptcha/api/siteverify
            post_data = {'secret': '6LfHKRMUAAAAAJG-cEV-SPcophf8jyXvrcghDtur', 'response': gcapcha}
            response = requests.post('https://www.google.com/recaptcha/api/siteverify', data=post_data)
            content = response.json()

            if not content['success']:
                return render(request, "interpay/index.html", {'error': _("Captcha is not entered.")})
        user = authenticate(username=username, password=password)

        user_user = models.User.objects.filter(username=username)
        if not user_user:
            return render(request, "interpay/index.html", {'error': _("Username or password is invalid.")})
        else:
            user_user = user_user[0]
        user_profile = models.UserProfile.objects.get(user=user_user)

        if user:
            if user.is_active and user_profile.is_active:
                login(request, user, None)
                if request.LANGUAGE_CODE == 'en-gb':
                    return HttpResponseRedirect(next)
                    # return HttpResponseRedirect('/home/')
                else:
                    return HttpResponseRedirect('/fa-ir' + next)
            else:
                if request.LANGUAGE_CODE == 'en-gb':
                    en_acc_disabled_msg = _("Your account is disabled.")
                    return render(request, 'interpay/index.html', {'msg': en_acc_disabled_msg})
                else:
                    fa_acc_disabled_msg = u'???? ?????? ??? ????? ??? ???.'
                    return render(request, 'interpay/index.html', {'msg': fa_acc_disabled_msg})
        else:
            print "Invalid login details: {0}, {1}".format(username, password)
            if request.LANGUAGE_CODE == 'en-gb':
                en_wrong_info_msg = _("Username or Password is not valid. please try again.")
                return render(request, 'interpay/index.html', {'msg': en_wrong_info_msg})
            else:
                fa_wrong_info_msg = u'??? ?????? ?? ??? ???? ???? ??? ?????? ???.'
                return render(request, 'interpay/index.html', {'msg': fa_wrong_info_msg})
    else:
        return render(request, 'interpay/index.html', {'next': next})


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
                name=cur + '_InterPay-account',
            )

            if created:
                user_b_account.account_id = make_id()
                user_b_account.save()

            banker = models.UserProfile.objects.get(user=models.User.objects.get(id=request.user.id))
            data = {"account_id": user_b_account.account_id, "amount": amnt, "banker_id": banker.id,
                    "date": str(datetime.datetime.utcnow()), "cur_code": cur}

            log.debug("new BankAccount object created and saved")
            zarinpal = zarinpal_payment_gate(request, amnt, user_profile.email, user_profile.mobile_number)
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
        if request.LANGUAGE_CODE == 'fa-ir':
            for transaction in deposit_set:
                cur_date =timezone.localtime(transaction.date)
                jalali_date_obj = GregorianToJalali(cur_date.year, cur_date.month, cur_date.day)
                year, month, day = jalali_date_obj.getJalaliList()
                transaction.date = str(year) + "-" + str(month) + "-" + str(day) + ", " + str(
                    cur_date.hour) + ":" + str(cur_date.minute) + ":" + str(cur_date.second)


    except Exception as e:
        log.debug('an exception occurred : ', e)
        deposit_set = models.Deposit.none()
    if code == -3:
        emessage = _("Entered value too small. This payment will not accept less than 100.")
    else:
        if code != 0:
            emessage = _("Unknown ZarinPal Error")
    print msg_color, "msg_color"
    deposit_num = deposit_set.count()
    return render(request, "interpay/top_up.html",
                  {'form': recharge_form, 'deposit_set': deposit_set, 'code': code, 'emessage': emessage,
                   'msg_color': msg_color, 'deposit_num': deposit_num})


MERCHANT_ID = 'd5dd997c-595e-11e6-b573-000c295eb8fc'
ZARINPAL_WEBSERVICE = 'https://sandbox.zarinpal.com/pg/services/WebGate/wsdl'  # real version : 'https://www.zarinpal.com/pg/services/WebGate/wsdl'
description = "this is a test"
# email = 'user@user.com'
# mobile = '09123456789'


def zarinpal_payment_gate(request, amount, email, mobile):

    amount = int(amount) / 10

    if request.LANGUAGE_CODE == 'en-gb':
        call_back_url = settings.SERVER_NAME + 'callback_handler/' + str(amount)  # TODO : this should be changed to our website url
    else:
        call_back_url = settings.SERVER_NAME + 'fa-ir/callback_handler/' + str(amount)  # TODO : this should be changed to our website url

    client = Client(ZARINPAL_WEBSERVICE)
    description = "pay to" + email
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
    global new_connection
    new_connection = settings.connect_to_redis()
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
                                     cur_code=a['cur_code'],
                                     tracking_code=result2.RefID, type=Deposit.TOP_UP)
            deposit.calculate_comission()  # automatically saves after calculating comission
            return recharge_account(request, message=_("Your account charged successfully"))

        elif result2.Status == 101:
            res = _("Transaction submitted : ") + str(result2.Status)
            # return render(request, 'interpay/test.html', {'res': res, 'result2': result2})
            return recharge_account(request, message=_("Your transaction has been successfully submitted earlier."))
        else:
            res = _("Transaction failed. Status: ") + str(result2.Status)
            # return render(request, 'interpay/test.html', {'res': res, 'result2': result2})
            return recharge_account(request, message=_("Your transaction was not successful. Try again later."))
    else:
        res = _("Transaction failed or canceled by user")
        # return render(request, 'interpay/test.html', {'res': res})
        return recharge_account(request, message=_("Transaction failed or canceled by you."))


@login_required()
def bank_accounts(request):
    user_profile = models.UserProfile.objects.get(user=request.user)
    mymessage = ''
    bank_account_form = CreateBankAccountForm(data=request.POST)
    irr_accounts = BankAccount.objects.filter(owner=user_profile, cur_code="IRR", method=BankAccount.DEBIT)

    if irr_accounts:
        irr_wallet = irr_accounts[0]
    else:
        irr_wallet = ""
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
                mymessage += _(": Error, that account has already been added.")

            new_account.save()
        else:
            if request.POST['account_id']:
                account = BankAccount.objects.get(account_id=request.POST['account_id'])
                amount = float(request.POST['amount'])
                account_id = request.POST['account_id']
                if account:

                    debit_accounts = BankAccount.objects.filter(owner=account.owner, method=1)
                    if not debit_accounts:
                        bank_account_form = CreateBankAccountForm()
                        bank_accounts_set = models.BankAccount.objects.filter(owner=user_profile,
                                                                              method=BankAccount.WITHDRAW)
                        return render(request, 'interpay/bank_accounts.html',
                                      {'error': _("No debit account."), 'bank_accounts_set': bank_accounts_set,
                                       'form': bank_account_form, 'emessage': mymessage, 'account_id': account_id,
                                       'irr_account': irr_wallet,
                                       })

                    bank_account_form = CreateBankAccountForm()
                    bank_accounts_set = models.BankAccount.objects.filter(owner=user_profile,
                                                                          method=BankAccount.WITHDRAW)

                    src_account = debit_accounts[0]
                    if src_account.balance < amount:
                        return render(request, 'interpay/bank_accounts.html', {'bank_accounts_set': bank_accounts_set,
                                                                               'form': bank_account_form,
                                                                               'emessage': mymessage,
                                                                               'error': _("Your balance is less than requested amount."),
                                                                               'account_id': account_id,
                                                                               'irr_account': irr_wallet,
                                                                               })
                    withdraw_request = WithdrawalRequest(src_account=src_account, dest_account=account, amount=amount)
                    withdraw_request.save()
                    return render(request, 'interpay/bank_accounts.html', {'bank_accounts_set': bank_accounts_set,
                                                                           'form': bank_account_form,
                                                                           'emessage': mymessage,
                                                                           'success_message': _("Your request successfully saved."),
                                                                           'account_id': account_id,
                                                                           'irr_account': irr_wallet,
                                                                           })

    bank_account_form = CreateBankAccountForm()
    bank_accounts_set = models.BankAccount.objects.filter(owner=user_profile, method=BankAccount.WITHDRAW) \
        .order_by('name')
    # irr_accounts = BankAccount.objects.filter(owner=user_profile, cur_code="IRR", method=BankAccount.DEBIT)
    #
    # if irr_accounts:
    #     irr_wallet = irr_accounts[0]
    # else:
    #     irr_wallet = ""
    print (irr_wallet.account_id, " ", irr_wallet.balance)
    return render(request, "interpay/bank_accounts.html", {
        'bank_accounts_set': bank_accounts_set,
        'form': bank_account_form,
        'emessage': mymessage,
        'irr_account': irr_wallet,
    })


@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect('/')


@login_required()
def home(request):
    user_profile = models.UserProfile.objects.get(user=request.user)
    notifications = Notification.objects.filter(user=user_profile, seen=False)
    context = {
        'accountList': BankAccount.objects.filter(owner=user_profile, method=BankAccount.DEBIT),
        'user_profile': user_profile,
        'notifications': notifications,
    }
    return render(request, "interpay/home.html", context)


class HomeView(TemplateView):
    template_name = 'interpay/home.html'


@login_required()
@cache_page(60)
@vary_on_headers('User-Agent', 'Cookie')
def wallets(request):
    print ("entered wallet")
    user_profile = models.UserProfile.objects.get(user=request.user)
    context = {

        'accountList': BankAccount.objects.filter(owner=user_profile, method=BankAccount.DEBIT),
        'user_profile': user_profile
    }
    return render(request, "interpay/wallets.html", context)


@login_required()
def wallet(request, wallet_id, recom=None):

    ba = BankAccount.objects.get(owner__user=request.user, account_id=wallet_id, method=BankAccount.DEBIT)
    up = ba.owner
    #assert(request.user.id==ba.owner.id)
    if request.method == "GET":
        recom = request.GET.get("recom")
        if recom is None:
            recommended = 0
        else:
            recommended = ba.balance
        transaction_list = []
        for item1 in Deposit.objects.filter(account=ba).select_related("payment_transfer"):
            transaction_list.append(item1)
        for item2 in Withdraw.objects.filter(account=ba):
            transaction_list.append(item2)
        # for item3 in MoneyTransfer.objects.filter(Q(receiver__owner=up) | Q(sender__owner=up)).filter(
        #                 Q(receiver=ba) | Q(sender=ba)):
        #     transaction_list.append(item3)
        transaction_list.sort(key=lambda x: x.date, reverse=True)
        if request.LANGUAGE_CODE == 'fa-ir':
          for transaction in transaction_list:
            cur_date = timezone.localtime(transaction.date)
            jalali_date_obj = GregorianToJalali(cur_date.year, cur_date.month, cur_date.day)
            year, month, day = jalali_date_obj.getJalaliList()
            transaction.date = str(year) + "-" + str(month) + "-" + str(day)+", " + str(cur_date.hour) + ":" + str(cur_date.minute) + ":" + str(cur_date.second)
        context = {
            'account': ba,
            'recommended': recommended,
            'list': transaction_list,
            'user_profile': up
        }

        return render(request, "interpay/wallet.html", context)


@login_required()
def withdraw_pending_deposit(request):
    if request.method == 'POST':
        log.debug("withdraw post")
        transaction_id = request.POST.get('selected_transaction_id')
        log.debug(transaction_id)
        deposit_id = request.POST.get('deposit_id' + str(transaction_id))
        #log.info(deposit_id)
        deposit = Deposit.objects.get(id=deposit_id)
        deposit.status = Deposit.COMPLETED
        deposit.save()
        account = deposit.account

        destination_currency = 'IRR'
        new_withdraw = Withdraw.objects.create(account=account, amount=deposit.amount, banker=account.owner,
                                               date=datetime.datetime.now(),
                                               cur_code=deposit.cur_code, type=Withdraw.CONVERSION)
        converted_amount = convert(deposit.amount, deposit.cur_code, destination_currency)
        rial_account = BankAccount.objects.filter(owner=account.owner, cur_code='IRR', method=BankAccount.DEBIT)
        if rial_account:
            print ("rial account")
            rial_account = rial_account[0]
        if not rial_account:
            print ("not rial account")
            rial_account = BankAccount.objects.create(name=destination_currency + '_InterPay-account', owner=account.owner,
                                                      method=BankAccount.DEBIT,
                                                      cur_code=destination_currency,
                                                      account_id=make_id())

        new_deposit = Deposit.objects.create(account=rial_account, amount=float(converted_amount), banker=account.owner,
                                             date=datetime.datetime.now(), cur_code=destination_currency,
                                             type=Deposit.CONVERSION)
        new_deposit.calculate_comission()
        conversion = CurrencyConversion.objects.create(deposit=new_deposit, withdraw=new_withdraw)
        print (new_deposit.account.account_id, " ", account.account_id)
        return HttpResponseRedirect('../')
        # context = {
        #     'account_id': account.id,
        #     'transaction_status': 'Requested amount was withdrawn successfully.',
        #     'account': account,
        #     'deposit_set': Deposit.objects.filter(account=account),
        #     'deposit_id': deposit.id,
        #     'withdraw_set': Withdraw.objects.filter(account=account),
        # }
        #
        # return render(request, 'interpay/wallet.html', context)
    return HttpResponseRedirect('../')


def check_currency_reserve(currency, amount):
    global new_connection
    new_connection = settings.connect_to_redis()
    currency_reserve = new_connection.get(currency)
    if currency_reserve:
        currency_reserve = float(currency_reserve)
        if currency_reserve < amount:
            return False
        else:
            return True
    else:
        try:
            current_currency = CurrencyReserve.objects.get(currency=currency)
            print (current_currency.reserve)
        except:
            return False
        if current_currency.reserve < amount:
            return False
        return True


@transaction.atomic()
@login_required()
def actual_convert(request):
    if request.method == 'POST':
        amount = request.POST.get('amount')
        currency = request.POST.get('currency')
        account_id = request.POST.get('account_id')
        cur_account = BankAccount.objects.get(account_id=account_id)
        if not check_currency_reserve(currency, convert(amount, cur_account.cur_code, currency)):
            return render(request, "interpay/wallet.html",
                          {
                              'error': _("This transaction is not possible now. Please try later."),
                              'account': BankAccount.objects.get(account_id=account_id),
                          })
        try:
            amount = float(amount)
        except ValueError:
            return render(request, "interpay/wallet.html",
                          {
                              'error': Validation.Validation.check_validation('invalid_amount'),
                              'account': BankAccount.objects.get(account_id=account_id),
                          })
        if amount <= 0:
            return render(request, "interpay/wallet.html",
                          {
                              'error': Validation.Validation.check_validation('non_positive'),
                              'account': BankAccount.objects.get(account_id=account_id),
                          })

        if cur_account.balance < amount:
            return render(request, "interpay/wallet.html",
                          {
                              'error': Validation.Validation.check_validation('insufficient_balance'),
                              'account': BankAccount.objects.get(account_id=account_id),
                          })
        user_profile = models.UserProfile.objects.get(user=request.user)
        conversion = CurrencyConversion()

        new_withdraw = Withdraw(account=cur_account, amount=amount, banker=user_profile, date=datetime.datetime.now(),
                                cur_code=cur_account.cur_code, type=Withdraw.CONVERSION)
        new_withdraw.save()
        conversion.withdraw = new_withdraw
        converted_amount = convert(amount, cur_account.cur_code, currency)
        destination_account = ""
        for temp_account in BankAccount.objects.filter(owner=user_profile, method=BankAccount.DEBIT):
            if temp_account.cur_code == currency:
                destination_account = temp_account
                break
        if not destination_account:
            destination_account = BankAccount(name=currency + '_InterPay-account', owner=user_profile, method=BankAccount.DEBIT,
                                              cur_code=currency,
                                              account_id=make_id())
        destination_account.save()
        new_deposit = Deposit(account=destination_account, amount=float(converted_amount), banker=user_profile,
                              date=datetime.datetime.now(), cur_code=currency, type=Deposit.CONVERSION)
        new_deposit.calculate_comission()
        new_deposit.save()
        conversion.deposit = new_deposit
        conversion.save()
        context = {
            'account_id': destination_account.account_id.__str__(),
            'message': _("Your new account created successfully. Your new account id is:") + destination_account.account_id.__str__(),
            'account': BankAccount.objects.get(account_id=account_id),
            'deposit_set': models.Deposit.objects.filter(account=cur_account),
        }
        return render(request, "interpay/wallet.html", context)
    else:
        return render(request, "interpay/wallet.html",
                      {
                          'error': _("Invalid GET Request. Contact Admin"),
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


def info(request):
    return render(request, "interpay/info.html")


def about(request):
    return render(request, "interpay/about.html")


def contact(request):
    return render(request, "interpay/contact.html")


def services(request):
    return render(request, "interpay/services.html")


@login_required()
def general(request):
    return render(request, "interpay/general.html")


def random_code_gen():
    verif_code = randint(100000, 999999)
    return verif_code


def handle_uploaded_file(f, filename):
    dir = os.path.dirname(filename)
    if not os.path.exists(dir):
        os.makedirs(dir)
    destination = open(filename, 'wb+')
    for chunk in f.chunks():
        destination.write(chunk)
    destination.close()


@csrf_exempt
def edit_profile(request):
    if request.is_ajax():
        if request.POST['action'] == 'change_name':
            entered_name = request.POST.get('name')
            user_profile = models.UserProfile.objects.get(user__username=request.user)
            user_profile.user.first_name = entered_name
            user_profile.user.save()
            html = '<strong>Your name has changed successfully</strong><hr>'
            result = {'html': html}
            return HttpResponse(json.dumps(result))
        if request.POST['action'] == 'change_last_name':
            entered_last_name = request.POST.get('last_name')
            user_profile = models.UserProfile.objects.get(user__username=request.user)
            user_profile.user.last_name = entered_last_name
            user_profile.user.save()
            html = '<strong>Your last name has changed successfully</strong><hr>'
            result = {'html': html}
            return HttpResponse(json.dumps(result))
        if request.POST['action'] == 'change_national_id':
            entered_naional_id = request.POST.get('national_id')
            user_profile = models.UserProfile.objects.get(user__username=request.user)
            user_profile.national_code = entered_naional_id
            user_profile.save()
            html = '<strong>Your National id has changed successfully</strong><hr>'
            result = {'html': html}
            return HttpResponse(json.dumps(result))

        if request.POST['action'] == 'change_username':
            entered_username = request.POST.get('username')
            user_profile = models.UserProfile.objects.get(user__username=request.user)
            user_profile.user.username = entered_username
            user_profile.user.save()
            html = '<strong>Your username has changed successfully</strong><hr>'
            result = {'html': html}
            return HttpResponse(json.dumps(result))


def contact_email(request):
    email = request.POST.get('email')
    title = request.POST.get('title')
    comment = request.POST.get('comment')
    send_mail(
        title,
        comment,
        email,
        ['info@rizpardakht.com'],
    )

    return HttpResponseRedirect(reverse('contact'))


@login_required()
def rating_by_email(request):
    email = request.GET.get('email')
    mobile = request.GET.get('mobile')
    response_data = {}
    userprofile = models.UserProfile.objects.get(email=email)
    log.debug("Getting rating by email")

    review_numbers = models.Review.objects.filter(user=userprofile).count()
    log.debug("Getting rating by email")

    # total_review = models.Review.objects.filter(user_id=user_id)
    print review_numbers
    total_rate = userprofile.review
    # review_numbers = 10
    response_data['result'] = total_rate.__str__()
    response_data['result2'] = review_numbers.__str__()

    return HttpResponse(
        json.dumps(response_data),
        content_type="application/json"
    )


@login_required()
def dynamic_rating(request):
    if request.method == 'POST':
        rate = request.POST.get('input_rate')
        mt_id = request.POST.get('review_moneytransfer_id')
        review_comment = request.POST.get('review_comment')

        monTrans = models.MoneyTransfer.objects.get(id=mt_id)
        # check if user__username should be used TODO
        reviewer = models.UserProfile.objects.get(user=request.user)
        print reviewer, rate,mt_id
        # user = ''
        if monTrans.withdraw.account.owner == reviewer:
            ty = "Buyer"
            account = monTrans.withdraw.account
            user = monTrans.deposit.account.owner

        else:
            ty = "Seller"
            account = monTrans.deposit.account
            user = monTrans.withdraw.account.owner

        print reviewer
        print ty
        created = True
        reviewing = None

        try:
            reviewing = models.Review.objects.get(money_transfer=monTrans)
        except models.Review.DoesNotExist:
            log.info("no previous review for this transaction")
            created = False
        if not created:
            reviewing = models.Review.objects.create(
                review=rate,
                comments=review_comment,
                type=ty,
                reviewer=reviewer,
                user=user,
                money_transfer=monTrans
            )
            reviewing.save()
        else:
            reviewing.review = rate
            reviewing.save()

        return HttpResponseRedirect(reverse('wallet', args=[account.account_id]))
        #return render(request,  "interpay/wallet.html")

@login_required()
def reviewing_id(request):
    email = request.GET.get('email')
    mobile = request.GET.get('mobile')
    response_data = {}
    reviewing_user_id = models.UserProfile.objects.get(email=email).id
    response_data['result'] = reviewing_user_id.__str__()

    return HttpResponse(
        json.dumps(response_data),
        content_type="application/json"
    )


@login_required()
def review_comments(request,reviewing_id):

    context = {
        'reviewList': Review.objects.filter(user=reviewing_id),
        'reviewing_user': UserProfile.objects.get(id=reviewing_id).user
    }
    return render(request, "interpay/review_comments.html", context)

favicon_view = RedirectView.as_view(url='/static/interpay/images/ipay-favicon.ico', permanent=True)

def unregistered_pay(request):
    return render(request, "interpay/unregistered_pay.html")

    # return render(request, "interpay/review_comments.html")

        # if request.POST['action'] == 'change_national_photo':
        # form_edit = RegistrationForm_edit(request.POST, request.FILES)
        # print form_edit
        # if form_edit.is_valid():
        # newphoto = form_edit.save(commit=False)
        # print newphoto
        # print request.FILES
        # newphoto.national_card_photo = request.FILES['national_card_photo']
        # newphoto.save()
        # print newphoto.national_card_photo
        # html = '<strong>Your National photo has changed successfully</strong><hr>'
        # result = {'html': html}
        # return HttpResponse(json.dumps(result))
        # if request.POST['action'] == 'change_national_photo':
        # form_edit = RegistrationForm_edit(request.POST, request.FILES)
        # print form_edit
        # if form_edit.is_valid():
        # newphoto = form_edit.save(commit=False)
        # print newphoto
        # print request.FILES
        # newphoto.national_card_photo = request.FILES['national_card_photo']
        # newphoto.save()
        # print newphoto.national_card_photo
        # html = '<strong>Your National photo has changed successfully</strong><hr>'
        # result = {'html': html}
        # return HttpResponse(json.dumps(result))



        # entered_naional_photo = request.POST.get('national_photo')
        # full_filename = os.path.join(settings.MEDIA_ROOT+"nationalCardScan/",entered_naional_photo)
        # registration_form_edit = RegistrationForm_edit(data=request.POST)


        # uploaded_filename = request.FILES[' national_photo'].name
        # print(uploaded_filename)
        # save the uploaded file inside that folder.
        # full_filename = os.path.join(settings.MEDIA_ROOT, folder, national_photo)
        # print(full_filename)


        # fout = open(full_filename, 'wb+')
        # file_content = ContentFile(request.FILES['national_photo'].read())
        # newdoc = handle_uploaded_file(request.FILES['national_photo'],full_filename)
        # print newdoc
        # print "you in"
        # newdoc.save()

        # Iterate through the chunks.
        # for chunk in file_content.chunks():
        #   fout.write(chunk)
        # fout.close()
        # user_profile = models.UserProfile.objects.get(user__username=request.user)
        # user_profile.national_card_photo = full_filename
        # user_profile.save()







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
