
from django.test import TestCase, Client
from interpay.models import User, UserProfile, BankAccount, Deposit
from currencies.models import Currency
import unittest
import datetime
from django.conf import settings


# from interpay.models import CurrencyConversion

# Create your tests here.

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
        self.assertEqual(accounts[1].balance, 3900000)


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


class ForgetPassword (TestCase):
    def test_fotgetpass(self):
        response = self.client.get("/login/")
        self.assertContains(response, 'Forgot password or account disabled')

class Registration (TestCase):
    def test_registration(self):
        c = Client()
        response = c.post('/register/', {'firstname': 'Negar','lastname':'goli', 'username': 'neg', 'mob_no':'09102376107'})
        self.assertContains(response, 'continue')