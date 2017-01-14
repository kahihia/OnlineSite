
from webbrowser import browser
from django.test import Client
from django.test import TestCase


class forgetpassword (TestCase):
  def testsetup(self):
   response = self.client.get("/login/")
   print(response.content)
   self.assertContains(response, 'Forgot password or account disabled')

  def test_wrong_password(self):
    response = self.client.get

# Create your tests here.

from django.contrib.auth.models import User
from interpay.models import *
user  = User.objects.get(username="salman")
up = UserProfile.objects.first()
sal  = User.objects.get(username="salman")
up.user = sal
up.save()
#ba =BankAccount(name='usdaccount', owner=up, method=BankAccount.DEBIT, cur_code='USD')
#ba.save()
ba = BankAccount.objects.get(owner=up,cur_code='USD')
ba.delete()
d=Deposit(account=ba,amount=1000.00,banker=up, date=datetime.now, cur_code='USD')
d.save()
print ba.balance

