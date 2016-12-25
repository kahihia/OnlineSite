from interpay.forms import RegistrationForm, UserForm, RechargeAccountForm
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
    user = models.User.objects.get(id=request.session['user_id'])
    #user = request.user
    while 1:
        try:
            user_profile = models.UserProfile.objects.get(user=user)
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
            user = models.User.objects.get(id=request.session['user_id'])
            user_profile = models.UserProfile.objects.get(user=user)
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
            user_b_account, created = models.BankAccount.objects.get_or_create(
                owner=user_profile,
                cur_code=cur,
                method=models.BankAccount.DEBIT,
                name=request.user.username + '_' + cur + '_account'
            )
            deposit = models.Deposit(account=user_b_account, total=amnt, banker=user_profile,
                                     when=user_b_account.when_opened, cur_code=cur)
            deposit.save()
            zarinpal = zarinpal_payment_gate(request, amnt)
            if zarinpal['status'] == 100:
                return redirect(zarinpal['ret'])
            return zarinpal['ret']
    recharge_form = RechargeAccountForm()

    user_profile = models.UserProfile.objects.get(user=models.User.objects.get(id=request.user.id))
    deposit_set = models.Deposit.objects.filter(banker=user_profile)
    return render(request, "top_up.html", {'form': recharge_form, 'deposit_set': deposit_set})


def zarinpal_payment_gate(request, amount):
    MMERCHANT_ID = 'd5dd997c-595e-11e6-b573-000c295eb8fc'
    ZARINPAL_WEBSERVICE = 'https://www.zarinpal.com/pg/services/WebGate/wsdl'  # test version : 'https://sandbox.zarinpal.com/pg/services/WebGate/wsdl'
    description = "this is a test"
    email = 'user@user.com'
    mobile = '09123456789'
    call_back_url = 'http://www.interpayafrica.com'  # this should be changed to our website url

    client = Client(ZARINPAL_WEBSERVICE)
    result = client.service.PaymentRequest(MMERCHANT_ID,
                                           amount,
                                           description,
                                           email,
                                           mobile,
                                           call_back_url)

    redirect_to = 'https://www.zarinpal.com/pg/StartPay/' + result.Authority  # the test vrsion : 'https://sandbox.zarinpal.com/pg/StartPay/'
    if result.Status != 100:
        redirect_to = 'Error'
    res = {'status': result.Status, 'ret': redirect_to}
    return res


def deposit_history_table(request):
    user_profile = models.UserProfile.objects.get(user=models.User.objects.get(id=request.user.id))
    deposit_set = models.Deposit.objects.filter(banker=user_profile)

    return deposit_set


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
