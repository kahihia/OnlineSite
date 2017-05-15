from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import staticfiles_storage
from django.http import HttpResponse
from django.test import TestCase, Client
from interpay.models import User, UserProfile, BankAccount, Deposit, MoneyTransfer, Withdraw
from currencies.models import Currency
from interpay.models import CurrencyReserve
import unittest
import datetime
from rest_framework.test import force_authenticate, APIRequestFactory
from django.conf import settings
from django.test.client import encode_multipart, RequestFactory
from django.core.urlresolvers import reverse, resolve
import json


# from interpay.models import CurrencyConversion

# Create your tests here.
class PaymentTestCase(TestCase):
    def setUp(self):
        user_src = User.objects.create_user(username='arman', password='1731', email='a@b.com', is_active=True)
        up_src = UserProfile.objects.create(user=user_src, date_of_birth=datetime.datetime.now(), email='a@b.com',
                                            is_active=True)

        user_dest = User.objects.create_user(username='arman71', password='1731', email='b@c.com', is_active=True)
        up_dest = UserProfile.objects.create(user=user_dest, date_of_birth=datetime.datetime.now(), email='b@c.com',
                                             is_active=True)
        src_account = BankAccount.objects.create(account_id="123", owner=up_src, cur_code='USD',
                                                 method=BankAccount.DEBIT)
        src_account.save()
        destination_account = BankAccount.objects.create(account_id="246", owner=up_dest, cur_code='USD',
                                                         method=BankAccount.DEBIT)
        destination_account.save()
        d = Deposit(account=src_account, amount=1000.00, banker=up_src, date=datetime.datetime.now(), cur_code='USD')
        d.save()
        cr1 = Currency.objects.create(code="USD", name="dollar")
        cr1.save()

    def test_payment(self):
        c = Client()
        c.login(username='arman', password='1731')
        response = c.get('/pay_user/')
        self.assertEqual(response.status_code, 200)
        post_response = c.post('/pay_user/',
                               {'currency': 'USD', 'amount': 100, 'email': 'b@c.com', 'comment': 'new payment',
                                'mobile': '10'})
        for temp in UserProfile.objects.all():
            print (temp.email, 'hfsjdhf')
        dest = UserProfile.objects.get(user__email='b@c.com')
        self.assertEqual(post_response.status_code, 200)
        dest_account = BankAccount.objects.get(owner=dest)
        # for temp in MoneyTransfer.objects.all():
        #     print (temp.amount, " ", temp.comment, " ", temp.sender.id, " ", temp.receiver.id, " ", temp.date)
        self.assertEqual(dest_account.balance, 100)

        post_response = c.post('/pay_user/',
                               {'currency': 'USD', 'amount': 1500, 'email': 'b@c.com', 'comment': 'new payment',
                                'mobile': '10'})
        self.assertEqual(post_response.context['error'], 'Your balance is not sufficient.')


class ConversionTestCase(TestCase):
    def setUp(self):
        print ("test started")
        user = User.objects.create_user(username='arman', password='1731', email='a@b.com', is_active=True)
        up = UserProfile.objects.create(user=user, date_of_birth=datetime.datetime.now(), is_active=True)
        ba = BankAccount.objects.create(account_id="123", owner=up, cur_code='USD')
        ba.save()
        d = Deposit(account=ba, amount=1000.00, banker=up, date=datetime.datetime.now(), cur_code='USD')
        d.save()
        cr1 = Currency.objects.create(code="USD", name="dollar")
        cr1.save()
        cr2 = Currency.objects.create(code="IRR", name="rial", factor=39000)
        cr2.save()
        CurrencyReserve.objects.create(currency="IRR", recharge_date=datetime.datetime.now(),
                                       on_recharge_amount=4000000)

    def test_conversion(self):
        c = Client()
        c.login(username='arman', password='1731')
        response = c.get('/wallets/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['accountList'][0].balance, 1000)
        post_response = c.post('/wallets/actual_convert/', {'account_id': '123', 'amount': 100, 'currency': 'IRR'})
        self.assertEqual(post_response.status_code, 200)
        accounts = BankAccount.objects.filter(owner__user__username="arman")
        self.assertEqual(accounts[0].balance, 900)
        self.assertEqual(accounts[1].balance, 3900000 - accounts[1].commission)


class LoginTestCase(TestCase):
    def setUp(self):
        print ("test started")
        user = User.objects.create_user(username='arman', password='1731', email='a@b.com', is_active=True)
        up = UserProfile.objects.create(user=user, date_of_birth=datetime.datetime.now(), is_active=True)
        settings.DEBUG = True

    def test_login(self):
        c = Client()
        # try:
        response = c.post('/login/', {'username': 'arman', 'password': '1731'})
        # except:
        #     print 'ignoring captcha exception for now'
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/home/')


class WithdrawalRequestTestCase(TestCase):
    def setUp(self):
        settings.DEBUG = True
        user = User.objects.create_user(username='arman', password='1731', email='a@b.com', is_active=True)
        up = UserProfile.objects.create(user=user, date_of_birth=datetime.datetime.now(), is_active=True,
                                        email='a@b.com', mobile_number='09102118797')
        ba = BankAccount.objects.create(account_id="123", owner=up, cur_code='USD', method=BankAccount.WITHDRAW)

    def test_no_debit(self):
        c = Client()
        c.login(username='arman', password='1731')
        account = BankAccount.objects.all()
        account_id = account[0].account_id
        response = c.post('/bank-accounts/',
                          {
                              'account_id': account_id,
                              'amount': 100
                          })
        self.assertEqual(response.context['error'], "No debit account.")


# class RegistrationTestCase(TestCase):
#     def setUp(self):
#         print ("test started")
#         settings.DEBUG = True
#         user = User.objects.create_user(username='arman', password='1731', email='a@b.com', is_active=True)
#         up = UserProfile.objects.create(user=user, date_of_birth=datetime.datetime.now(), is_active=True,
#                                         email='a@b.com', mobile_number='09102118797')
#
#     def test_sign_up(self):
#         c = Client()
#
#         response = c.post('/register/',
#                           {'username': 'ali', 'first_name': 'Ali', 'last_name': 'Alavi', 'email': 'ali@gmail.com',
#                            'password': '1731', 'confirm_password': '1731', 'date_of_birth': datetime.date(1920, 1, 1),
#                            'country': 'AF',
#                            'national_code': '0440282322', 'mobile_number': '09125779876'})
#         user = UserProfile.objects.all()
#         self.assertEqual(user.__len__(), 2)


class APITestCase(TestCase):
    def setUp(self):
        print ("test started")
        settings.DEBUG = True
        user = User.objects.create_user(username='arman', password='1731', email='a@b.com', is_active=True)
        up = UserProfile.objects.create(user=user, date_of_birth=datetime.datetime.now(), is_active=True,
                                        email='a@b.com', mobile_number='09102118797')

    def test_cash_out(self):
        content = {'payeeEmail': 'a@b.com', 'orderAmount': '150', 'MerOrderRef': '500',
                   'orderCurrencyCode': 'EUR', 'payeeMobile': '09102118797',
                   'Authorization': 'Token 013799913a41292f31a4173ba58e10a2d6f26ad1'}
        data = self.make_request('/rest_framework/cash_out_order/', content, 'cash_out')
        self.assertEqual(data['status'], 'pending')
        self.assertEqual(data['orderAmount'], '150')

    def test_not_existing_user(self):
        content = {'payeeEmail': 'a@c.com', 'orderAmount': '150', 'MerOrderRef': '500',
                   'orderCurrencyCode': 'EUR', 'payeeMobile': '09102118778',
                   'Authorization': 'Token 013799913a41292f31a4173ba58e10a2d6f26ad1'}
        data = self.make_request('/rest_framework/cash_out_order/', content, 'cash_out')
        self.assertEqual(data['statusCode'], 4)
        self.assertEqual(data['statusMessage'], 'New user was created in system.')

    def test_get_order_status(self):
        self.cash_out_request()
        order_status_content = {'MerOrderRef': '500',
                                'orderReference': 1}
        data = self.make_request('/rest_framework/get_order_status/', order_status_content, 'order_status')
        self.assertEqual(data['status_message'], 'pending')
        self.assertEqual(data['orderAmount'], 150)

    def test_cash_out_reversal(self):
        self.cash_out_request()

        cash_out_reversal_content = {'MerOrderRef': '500',
                                     'orderReference': 1}
        data = self.make_request('/rest_framework/cash_out_reversal/', cash_out_reversal_content, 'cash_out_reversal')
        deposit = Deposit.objects.all()[0]
        self.assertEqual(deposit.status, 1)

    def test_unsuccessful_cash_out_reversal(self):
        self.cash_out_request()
        deposit = Deposit.objects.all()[0]
        deposit.status = 3
        deposit.save()
        cash_out_reversal_content = {'MerOrderRef': '500',
                                     'orderReference': 1}
        data = self.make_request('/rest_framework/cash_out_reversal/', cash_out_reversal_content, 'cash_out_reversal')
        self.assertEqual(data['statusMessage'], 'Transaction was unsuccessful. Money has been withdrawn.')

    def test_get_pending_orders(self):
        self.cash_out_request()
        get_pending_orders_content = {'MerOrderRef': '500',
                                      'orderReference': 1,
                                      'size': 50,
                                      'sort': 60,
                                      'page': 1}
        data = self.make_request('/rest_framework/get_pending_orders/', get_pending_orders_content,
                                 'get_pending_orders')
        orders = data['orders']
        json_orders = json.loads(orders)
        self.assertEqual(json_orders[0]['status'], 'Pending')
        # print (json_orders[0]['status'])

    def test_get_pending_orders_no_order(self):
        get_pending_orders_content = {'MerOrderRef': '500',
                                      'orderReference': 1,
                                      'size': 50,
                                      'sort': 60,
                                      'page': 1}
        data = self.make_request('/rest_framework/get_pending_orders/', get_pending_orders_content,
                                 'get_pending_orders')
        self.assertEqual(data['statusMessage'], 'There is no request in specified range.')

    def cash_out_request(self):
        cash_out_content = {'payeeEmail': 'a@b.com', 'orderAmount': '150', 'MerOrderRef': '500',
                            'orderCurrencyCode': 'EUR', 'payeeMobile': '09102118797',
                            'Authorization': 'Token 013799913a41292f31a4173ba58e10a2d6f26ad1'}
        self.make_request('/rest_framework/cash_out_order/', cash_out_content, 'cash_out')

    def make_request(self, url, content, url_name):
        factory = APIRequestFactory()
        request = factory.post(url, content, format='json')
        user = User.objects.get(username='arman')
        force_authenticate(request, user=user)
        func_url = reverse(url_name)
        view = resolve(func_url).func
        response = view(request)
        return json.loads(response.content)


class ForgetPassword(TestCase):
    def test_forgetpass(self):
        response = self.client.get("/login/")
        self.assertContains(response, 'Forgot password or account disabled')


class Registration(TestCase):
    def test_registration(self):
        c = Client()
        response = c.post('/register/',
                          {'firstname': 'Negar', 'lastname': 'goli', 'username': 'neg', 'mob_no': '09102376107'})
        self.assertContains(response, 'continue')


class CallbackTestCase(TestCase):
    def setUp(self):
        user_src = User.objects.create_user(username='arman', password='1731', email='a@b.com', is_active=True)
        up_src = UserProfile.objects.create(user=user_src, date_of_birth=datetime.datetime.now(), email='a@b.com',
                                            is_active=True)

        user_dest = User.objects.create_user(username='arman71', password='1731', email='b@c.com', is_active=True)
        up_dest = UserProfile.objects.create(user=user_dest, date_of_birth=datetime.datetime.now(), email='b@c.com',
                                             is_active=True)
        src_account = BankAccount.objects.create(account_id="123", owner=up_src, cur_code='USD',
                                                 method=BankAccount.DEBIT)
        src_account.save()
        destination_account = BankAccount.objects.create(account_id="246", owner=up_dest, cur_code='USD',
                                                         method=BankAccount.DEBIT)
        destination_account.save()
        d = Deposit(account=src_account, amount=1000.00, banker=up_src, date=datetime.datetime.now(), cur_code='USD')
        d.save()
        cr1 = Currency.objects.create(code="USD", name="dollar")
        cr1.save()

    def test_callback(self):
        c = Client()
        c.login(username='arman', password='1731')


class Teststaticfiles(TestCase):
    def test_responsive(self):
        abs_path = finders.find('../static/interpay/css/logo.css')
        # print ("abspath"+abs_path)
        #self.assertTrue(staticfiles_storage.exists(settings.BASE_DIR + '/static/interpay/css/logo.css'))
        #test_file = open(abs_path, 'rb')
        #self.assertIs('@media only screen and (min-width : 420px) and ( max-width: 900px)' in test_file.read(), True)


class ReviewTestCase(TestCase):
    def setUp(self):
        print ("review test started")

        user1 = User.objects.create_user(username='z1', password='z1', is_active=True)
        up_user1 = UserProfile.objects.create(user=user1, date_of_birth=datetime.datetime.now(), is_active=True,
                                              email='z1@gmail.com')
        up_user1.save()

        user2 = User.objects.create_user(username='a1', password='a1', is_active=True)
        up_user2 = UserProfile.objects.create(user=user2, date_of_birth=datetime.datetime.now(), is_active=True,
                                              email='a1@gmail.com')
        up_user2.save()

        reviewer = BankAccount.objects.create(account_id="123", owner=up_user1, cur_code='USD',
                                              method=BankAccount.DEBIT)
        reviewer.save()
        reviewing = BankAccount.objects.create(account_id="456", owner=up_user2, cur_code='USD',
                                               method=BankAccount.DEBIT)
        reviewing.save()

        deposit_user = Deposit.objects.create(account=reviewer, amount=200, banker=up_user1, date=datetime.datetime.now(

        ), )
        deposit_user.save()

        withdraw_user = Withdraw.objects.create(account=reviewing, amount=200, banker=up_user2)
        withdraw_user.save()

        montrans = MoneyTransfer.objects.create(deposit=deposit_user, withdraw=withdraw_user, comment="dinner")
        montrans.save()

    def test_review(self):
        c = Client()
        c.login(username='z1', password='z1')
        post_response = c.post('/dynamic_rating/',
                               {'review_moneytransfer_id': '1', 'input_rate': '4', 'review_comment': 'good'})
        self.assertRedirects(post_response, reverse('wallet', args=["123"]), status_code=302, target_status_code=200,
                             fetch_redirect_response=True)

    def test_review_show(self):
        c = Client()
        c.login(username='z1', password='z1')
        get_response = c.get('/rating_by_email/', {'email': 'a1@gmail.com', 'mobile': '09123312087'})
        self.assertEqual(get_response.status_code, 200)


class TestWithdrawInternationalPayment(TestCase):
    def setUp(self):
        settings.DEBUG = True
        user = User.objects.create_user(username='arman', password='1731', email='a@b.com', is_active=True)
        up = UserProfile.objects.create(user=user, date_of_birth=datetime.datetime.now(), is_active=True,
                                        email='a@b.com', mobile_number='09102118797')
        content = {'payeeEmail': 'a@b.com', 'orderAmount': '150', 'MerOrderRef': '500',
                   'orderCurrencyCode': 'EUR', 'payeeMobile': '09102118797',
                   'Authorization': 'Token 013799913a41292f31a4173ba58e10a2d6f26ad1'}
        data = self.make_request('/rest_framework/cash_out_order/', content, 'cash_out')
        cr1 = Currency.objects.create(code="EUR", name="dollar")
        cr1.save()
        cr2 = Currency.objects.create(code="IRR", name="rial", factor=39000)
        cr2.save()
        CurrencyReserve.objects.create(currency="IRR", recharge_date=datetime.datetime.now(),
                                       on_recharge_amount=400000000)

    def make_request(self, url, content, url_name):
        factory = APIRequestFactory()
        request = factory.post(url, content, format='json')
        user = User.objects.get(username='arman')
        force_authenticate(request, user=user)
        func_url = reverse(url_name)
        view = resolve(func_url).func
        response = view(request)
        return json.loads(response.content)

    def test_withdraw(self):
        up = UserProfile.objects.all()[0]
        deposit = Deposit.objects.all()[0]
        c = Client()
        c.login(username='arman', password='1731')
        post_response = c.post('/wallets/withdraw_pending_deposit/',
                               {'selected_transaction_id': deposit.id, 'deposit_id' + str(deposit.id): deposit.id})
        rial_wallet = BankAccount.objects.get(cur_code="IRR")
        self.assertEqual(rial_wallet.balance + rial_wallet.commission, float(5850000))


class DirectPayTestCase(TestCase):

    def SenderExist(self):
        sender_user = User.objects.create(username='z1', password='123', is_active=True)
        sender_user_profile = UserProfile.objects.create(user=sender_user, date_of_birth=datetime.datetime.now(), is_active=True,
                                              email='z1@gmail.com', mobile_number='09123312087' )
        content = {'amount': '10000', 'sender_email': 'z1@gmail.com', 'sender_mobile': '09123312087',
                   'receiver_email': 'z2@gmail.com', 'receiver_mobile': '09124313015', 'comment': 'book'}
        c = Client()
        data = c.post('/unregistered_charge/', content)
        self.assertEqual(data.status_code, 200)

    def ReceiverExist(self):
        receiver_user = User.objects.create(username='z2', password='123', is_active=True)
        receiver_user_profile = UserProfile.objects.create(user=receiver_user, date_of_birth=datetime.datetime.now(),
                                                         is_active=True,
                                                         email='z2@gmail.com', mobile_number='09124313015')
        receiver_user_account = BankAccount.objects.create(owner=receiver_user_profile, method=BankAccount.DEBIT,
                                                         cur_code='IRR', account_id=1,
                                                         name='IRR_InterPay-account')
        content = {'amount': '10000', 'sender_email': 'z1@gmail.com', 'sender_mobile': '09123312087',
                   'receiver_email': 'z2@gmail.com', 'receiver_mobile': '09124313015', 'comment': 'book'}
        c = Client()
        data = c.post('/unregistered_charge/', content)
        self.assertEqual(data.status_code, 302)

    def NewSenderReceiver(self):
        content = {'amount': '10000', 'sender_email': 'z1@gmail.com', 'sender_mobile': '09123312087',
                   'receiver_email': 'z2@gmail.com', 'receiver_mobile': '09124313015', 'comment': 'book'}
        c = Client()
        data = c.post('/unregistered_charge/', content)
        self.assertEqual(data.status_code, 302)



