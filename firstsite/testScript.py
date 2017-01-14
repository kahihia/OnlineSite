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