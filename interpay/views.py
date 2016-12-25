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
from interpay.models import BankAccount
from random import randint
from suds.client import Client
import json
import time
import random


def main_page(request):

    if request.user.is_authenticated():
        return home(request)
    return render(request, 'index.html')


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
        return render(request, 'registeration_form.html',
                      {'user_form': user_form, 'profile_form': registration_form,
                       'registered': registered,
                       'thanks_msg': thanks_msg, 'redirect_to_home_msg': redirect_to_home_msg, 'activated': activated})
    else:
        thanks_msg = "???? ?????? ??? ?? ?????? ????? ??."
        redirect_to_home_msg = '???? ???? ??? ?? ??????.'
        # dict = {thanks_msg, redirect_to_home_msg}
        return render(request, 'registeration_form.html',
                      {'user_form': user_form, 'profile_form': registration_form,
                       'registered': registered,
                       'thanks_msg': thanks_msg, 'redirect_to_home_msg': redirect_to_home_msg, 'activated': activated})


@csrf_exempt
def send_sms(request, mobile_no):
    # TODO : make mobile_no an optional input argument
    mobile_no = request.session['mobile_no']
    #
    request.session['try_counter'] = 0
    code = random_code_gen()
    request.session['code'] = code
    # redis_ds = ds.AuthCodeDataStructure()
    # redis_ds.set_code(mobile_no, code)
    p = api.ParsGreenSmsServiceClient()
    api.ParsGreenSmsServiceClient.sendSms(p, code=code, mobile_no=mobile_no)
    
    #user = request.user
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
        sent_code = request.session['code']
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
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)
        user_user = models.User.objects.get(username=username)
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
                    return render(request, 'index.html', {'msg': en_acc_disabled_msg})
                else:
                    fa_acc_disabled_msg = u'???? ?????? ??? ????? ??? ???.'
                    return render(request, 'index.html', {'msg': fa_acc_disabled_msg})
        else:
            print "Invalid login details: {0}, {1}".format(username, password)
            if request.LANGUAGE_CODE == 'en-gb':
                en_wrong_info_msg = "Username or Password is not valid. please try again."
                return render(request, 'index.html', {'msg': en_wrong_info_msg})
            else:
                fa_wrong_info_msg = u'??? ?????? ?? ??? ???? ???? ??? ?????? ???.'
                return render(request, 'index.html', {'msg': fa_wrong_info_msg})
    else:
        return render(request, 'index.html', {})


@login_required()
def recharge_account(request):
    recharge_form = RechargeAccountForm(data=request.POST)
    if request.method == 'POST':
        if recharge_form.is_valid():
            cur = recharge_form.cleaned_data['currency']
            amnt = recharge_form.cleaned_data['amount']
            print amnt, cur, request.user, request.user.id, request.user.username
            user_profile = models.UserProfile.objects.get(user=models.User.objects.get(id=request.user.id))
            # TODO : this part should be edited to check whether there is already an account with this name; if so, increament the account's total
            user_b_account, created = models.BankAccount.objects.get_or_create(
                owner=user_profile,
                cur_code=cur,
                method=models.BankAccount.DEBIT,
                name=request.user.username + '_' + cur + '_InterPay-account',
                account_id=make_id()
            )
            deposit = models.Deposit(account=user_b_account, amount=amnt, banker=user_profile,
                                     date=user_b_account.when_opened, cur_code=cur)
            deposit.save()
            zarinpal = zarinpal_payment_gate(request, amnt)
            if zarinpal['status'] == 100:
                return redirect(zarinpal['ret'])
            return zarinpal['ret']
    recharge_form = RechargeAccountForm()

    user_profile = models.UserProfile.objects.get(user=models.User.objects.get(id=request.user.id))
    deposit_set = models.Deposit.objects.filter(banker=user_profile)
    return render(request, "top_up.html", {'form': recharge_form, 'deposit_set': deposit_set})


START_TIME = 0x0


def make_id():
    '''
    inspired by http://instagram-engineering.tumblr.com/post/10853187575/sharding-ids-at-instagram
    '''

    t = int(time.time() * 1000) - START_TIME
    u = random.SystemRandom().getrandbits(22)
    id = (t << 22) | u
    return id


def zarinpal_payment_gate(request, amount):
    MERCHANT_ID = 'd5dd997c-595e-11e6-b573-000c295eb8fc'
    ZARINPAL_WEBSERVICE = 'https://www.zarinpal.com/pg/services/WebGate/wsdl'  # test version : 'https://sandbox.zarinpal.com/pg/services/WebGate/wsdl'
    description = "this is a test"
    email = 'user@user.com'
    mobile = '09123456789'
    call_back_url = 'http://www.interpayafrica.com'  # TODO this should be changed to our website url

    client = Client(ZARINPAL_WEBSERVICE)
    result = client.service.PaymentRequest(MERCHANT_ID,
                                           amount,
                                           description,
                                           email,
                                           mobile,
                                           call_back_url)
    redirect_to = 'https://www.zarinpal.com/pg/StartPay/' + str(
        result.Authority)  # the test version : 'https://sandbox.zarinpal.com/pg/StartPay/'
    if result.Status != 100:
        redirect_to = 'Error'
    res = {'status': result.Status, 'ret': redirect_to}
    verify(request, result.Status, result.Authority, amount, MERCHANT_ID, ZARINPAL_WEBSERVICE)
    return res


def verify(request, status, authority, amount, merchant_id, zarinpal_webservice):
    client = Client(zarinpal_webservice)
    print request.GET.get
    result2 = client.service.PaymentVerificationWithExtra(merchant_id,
                                                          authority,
                                                          amount)
    print result2.RefID, result2.Status, result2.ExtraDetail
    # if request.GET.get('Status') == 'OK':
    #     result = client.service.PaymentVerification(merchant_id,
    #                                                 authority,
    #                                                 amount)
    if result2.Status == 100:
        print 'Transaction success. RefID: ' + str(result2.RefID)
    elif result2.Status == 101:
        print 'Transaction submitted : ' + str(result2.Status)
    else:
        print 'Transaction failed. Status: ' + str(result2.Status)
        # else:
        #     return 'Transaction failed or canceled by user'


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
            print bank_name, cur, request.user, request.user.id, request.user.username
            new_account = models.BankAccount(
                owner=user_profile,
                cur_code=cur,
                method=1,
                name=bank_name,
                account_id=account_no,
            )
            new_account.save()
    bank_account_form = CreateBankAccountForm()
    bank_accounts_set = models.BankAccount.objects.filter(owner=user_profile)
    return render(request, "bank_accounts.html", {'bank_accounts_set': bank_accounts_set, 'form': bank_account_form})


@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect('/')


@login_required()
def home(request):
    return render(request, "home.html")


class HomeView(TemplateView):
    template_name = 'home.html'


@login_required()
def wallets(request):
    user_profile = models.UserProfile.objects.get(user=request.user)
    context = {

        'accountList': BankAccount.objects.filter(owner=user_profile),
        'user_profile':user_profile
    }
    return render(request, "wallets.html", context)


@login_required()
def trans_history(request):
    return render(request, "trans_history.html")


@login_required()
def reports(request):
    return render(request, "reports.html")


@login_required()
def general(request):
    return render(request, "general.html")


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
