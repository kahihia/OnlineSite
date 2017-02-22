from django.test import TestCase, Client
from interpay.models import User, UserProfile, BankAccount, Deposit, MoneyTransfer
from currencies.models import Currency
import unittest
import datetime
from django.conf import settings
from rest_framework.test import force_authenticate, APIRequestFactory
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
        for temp in MoneyTransfer.objects.all():
            print (temp.amount, " ", temp.comment, " ", temp.sender.id, " ", temp.receiver.id, " ", temp.date)
        self.assertEqual(dest_account.balance, 100)

        post_response = c.post('/pay_user/',
                               {'currency': 'USD', 'amount': 1500, 'email': 'b@c.com', 'comment': 'new payment',
                                'mobile': '10'})
        # print (post_response.context['error'],'fasdfasdf')
        # print (dest_account.)
        self.assertEqual(post_response.context['error'], 'Your balance is less than entered amount.')
        # cr2 = Currency.objects.create(code="IRR", name="rial", factor=39000)
        # cr2.save()


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
        self.assertEqual(data['statusCode'], 3)
        self.assertEqual(data['statusMessage'], 'No user with specified information.')

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


# class ForeignKeyTestCase(TestCase):
#     def setUp(self):
#         user_src = User.objects.create_user(username='arman', password='1731', email='a@b.com', is_active=True)
#         up_src = UserProfile.objects.create(user=user_src, date_of_birth=datetime.datetime.now(), email='a@b.com',
#                                             is_active=True)
#
#         user_dest = User.objects.create_user(username='arman71', password='1731', email='b@c.com', is_active=True)
#         up_dest = UserProfile.objects.create(user=user_dest, date_of_birth=datetime.datetime.now(), email='b@c.com',
#                                              is_active=True)
#         account1 = BankAccount.objects.create(account_id="123", owner=up_src, cur_code='USD',
#                                               method=BankAccount.DEBIT)
#         account2 = BankAccount.objects.create(account_id="124", owner=up_src, cur_code='USD',
#                                               method=BankAccount.DEBIT)
#         account3 = BankAccount.objects.create(account_id="125", owner=up_src, cur_code='USD',
#                                               method=BankAccount.DEBIT)
#         account4 = BankAccount.objects.create(account_id="126", owner=up_src, cur_code='USD',
#                                               method=BankAccount.DEBIT)
#         MoneyTransfer.objects.create(sender=account1, receiver=account2,
#                                      date=datetime.datetime.now(),
#                                      amount=100, comment="test", cur_code="USD")
#         MoneyTransfer.objects.create(sender=account1, receiver=account2,
#                                      date=datetime.datetime.now(),
#                                      amount=200, comment="test", cur_code="USD")
#         MoneyTransfer.objects.create(sender=account1, receiver=account2,
#                                      date=datetime.datetime.now(),
#                                      amount=300, comment="test", cur_code="USD")
#         for temp in account1.outcome_transfers.all():
#             print ("abcde")
#         for temp in account3.outcome_transfers.all():
#             print ("abcdefgh")
#
#     def test_payment(self):
#         print ("test started")


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
        # response = c.get('/fa-ir/top-up/')
        # self.assertEqual(response.status_code, 200)
        # # print "***************"
        # # print response
        # post_response = c.get('/callback_handler/',
        #                       {'Status': 'OK', 'amount': 100, 'email': 'b@c.com', 'comment': 'new payment',
        #                        'mobile': '10'})
        # self.assertEqual(post_response.status_code, 200)
