from django.contrib.auth.models import User
from interpay.models import *
from django.core.management.base import BaseCommand, CommandError
import datetime


# setups the default users that are used in pay_user.html

class Command(BaseCommand):
    help = 'obtains the latest rates from sarafi'

    def create_user_c(self, name , memail):
        user = User.objects.create_user(username=name, password='96interpay96', email=memail, is_active=True)
        up = UserProfile.objects.create(user=user, date_of_birth=datetime.datetime.now(), email=memail,
                                        is_active=True)
        user.save()
        up.save()

    def handle(self, *args, **options):
        name = "googleplay"
        memail = "googleplay@rizpardakht.com"
        mobile = ""

        self.create_user_c(name, memail)
        self.create_user_c("gmat", "gmat@rizpardakht.com")
        self.create_user_c("gre2", "gre2@rizpardakht.com")
        self.create_user_c("uni", "gre@rizpardakht.com")

