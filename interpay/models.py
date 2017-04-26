from django.contrib.auth.base_user import BaseUserManager
from django.core.mail import send_mail
from django.core.validators import RegexValidator, int_list_validator
from django.utils.encoding import force_text
from django.core.validators import RegexValidator
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.db import models
from django.forms import ChoiceField
from django_countries.fields import CountryField
from django.utils import timezone
from django.contrib.auth.models import User
from django.utils.formats import get_format
from datetime import datetime, timedelta
from django.core.mail import send_mail
from collections import defaultdict
from currencies.utils import convert
from choices import TYPE_CHOICES
from firstsite import settings
from django.db import models
from decimal import Decimal
# import convert
import random
import time
import logging

log = logging.getLogger('interpay')


class Manager(BaseUserManager):
    def create_user(self, USERNAME_FIELD, email, password):
        email = self.normalize_email(email)
        username = self.model.normalize_username(USERNAME_FIELD)
        user = self.model(username=username, email=email)
        user.set_password(password)
        user.save(using=self._db)
        return user


class UserProfile(models.Model):
    user = models.OneToOneField(User, related_name="UserProfile")
    password = models.CharField(max_length=10, null=False, blank=False)
    picture = models.ImageField(upload_to='userProfiles/', null=True, blank=True)
    date_of_birth = models.DateTimeField(null=False, blank=False)
    date_joined = models.DateTimeField(default=datetime.now())
    country = CountryField(default="Iran")
    national_card_photo = models.ImageField(upload_to='nationalCardScans/', default='nationalCardScans/def.jpg',null=True, blank=True)
    national_code = models.CharField(max_length=10, null=False, blank=False)
    mobile_number = models.CharField(max_length=11, null=True, blank=True)
    email = models.EmailField(null=False, blank=False)
    # TODO : this field should not be nullable. fix it.
    is_active = models.BooleanField(default=False)

    USERNAME_FIELD = 'username'

    objects = Manager()

    def email_user(self, subject, message, from_email=None, **kwargs):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def __str__(self):
        return '{}'.format(self.user.username)

    def __unicode__(self):
        return self.user.username

        # def __init__(self, *args, **kwargs):
        #     super(UserProfile, self).__init__(*args, **kwargs)
        #     if self.instance:
        #         # we're operating on an existing object, not a new one...
        #         country = self.instance.country
        #         cities = self.fields["new_city"] = ChoiceField(choices=cities)


class CommonUser(models.Model):
    # since we might need to define a Manager model in the future, this model is named as "CommonUser"
    user_ID = models.ForeignKey(UserProfile, null=False, related_name='user_ID')

    def __str__(self):
        return '{} - {}'.format(self.customer_ID, self.user_ID.name)


class VerificationCodes(models.Model):
    user_code = models.IntegerField()
    user = models.ForeignKey(UserProfile, null=False, related_name='verif_code_user')

    # def __str__(self):
    #     return '{} - {}'.format(self.user, self.user.name)


class Rule(models.Model):
    my_formats = get_format('DATETIME_INPUT_FORMATS')
    start_date = models.DateField()  # (required=False, input_formats=('%d/%m/%Y',))#(input_formats="%d-%b-%Y")
    end_date = models.DateField()  # (input_formats="%d-%b-%Y")
    # end_date = models.DateField()
    cur_code = models.CharField(_('cur_code'), max_length=3, default='USD')
    deposit_charge_percent = models.FloatField(default=4)
    credit_percent = models.FloatField(default=98)

    @staticmethod
    def on_date_s(_date, _code='USD'):
        r = None
        try:
            # print _date, _code
            r = Rule.objects.get(start_date__lte=_date, end_date__gte=_date, cur_code=_code)

        except Rule.DoesNotExist:
            log.info('Warning: default comission rule is being used')
            r = Rule(cur_code=_code, start_date=datetime.now().date(),
                     end_date=(datetime.now() + timedelta(days=1)).date())

        return r


START_TIME = 0x0


def make_id():
    '''
    inspired by http://instagram-engineering.tumblr.com/post/10853187575/sharding-ids-at-instagram
    '''

    t = int(time.time() * 1000) - START_TIME
    u = random.SystemRandom().getrandbits(22)
    id = (t << 22) | u

    return id


def reverse_id(id):
    t = id >> 22
    return t + START_TIME


class BankAccount(models.Model):
    LEGAL = 1
    INDIVIDUAL = 2
    DEBIT = 1
    WITHDRAW = 2

    # owner_type = models.PositiveSmallIntegerField(choices=(
    #     (LEGAL, 'Legal'),
    #     (INDIVIDUAL, 'INDIVIDUAL'),
    # ), default=INDIVIDUAL)

    method = models.PositiveSmallIntegerField(choices=(
        (DEBIT, 'Debit'),
        (WITHDRAW, 'Withdraw'),
    ), default=DEBIT)
    alphanumeric = RegexValidator(r'^[0-9a-zA-Z]*$', 'Only alphanumeric characters are allowed.')
    # TODO : this validator should be placed in js as well, so the user can not type other kinds of inputs
    name = models.CharField(max_length=254)
    when_opened = models.DateField(_("Date"), default=datetime.now)
    owner = models.ForeignKey(UserProfile, related_name='w_accounts')
    cur_code = models.CharField(_('cur_code'), max_length=3, default='IRR')
    spectators = models.ManyToManyField(UserProfile, related_name='r_accounts')
    account_id = models.CharField(max_length=24)

    def total_value(self):
        t_value = Decimal(0)
        total_estimate = defaultdict(lambda: Decimal(0.0))
        accounts = BankAccount.objects.filter(owner=self.owner, method=BankAccount.DEBIT)
        for account in accounts:
            total_estimate[account.cur_code] = Decimal(convert(account.balance, account.cur_code, 'USD'))
            t_value += total_estimate[account.cur_code]

        return t_value.quantize(Decimal("0.01"))
        # TODO define total value

    @property
    def balance(self):
        assert self.method == self.DEBIT
        today = datetime.today()

        current_date = self.when_opened
        # print 'started while'
        result = 0
        while current_date <= datetime.date(today):
            # print self.deposit_set.count()
            # print 'count of sets fix withdraw outcome then deposit'

            result -= sum(x.amount for x in self.withdraw_set.all())
            # result -= sum(x.amount for x in self.outcome_transfers.all())  # .on_date_out(current_date, self))

            # result += sum(x.amount for x in self.deposit_set.on_date_c(current_date, self.cur_code, self))
            # result += sum(x.amount for x in self.deposit_set.all())
            dep_set = self.deposit_set.filter(status=Deposit.COMPLETED)
            result += sum(x.amount for x in dep_set)
            # result += sum(x.commission for x in dep_set)  No need to sum comission as amount = total - comission
            # result += sum(x.amount for x in self.income_transfers.all())  # on_date_in(current_date, self))

            current_date += timedelta(days=1)
            break

        if self.cur_code=='IRR':
            return round(result, 0)
        else:
            return round(result, 2)

    @property
    def commission(self):
        result = 0
        dep_set = self.deposit_set.filter(status=Deposit.COMPLETED)
        result += sum(x.commission for x in dep_set)
        return result



        # @property
        # def debt(self):
        #     assert self.method == self.CREDIT
        #     today = time.timezone.now()
        #     rule = Rule.on_date(self.when_opened)
        #     result = 0
        #     current_date = self.when_opened
        #     while current_date <= today:
        #         result += sum(x.amount for x in self.withdraw_set.on_date(current_date))
        #         result += sum(x.amount for x in self.outcome_transfers.on_date(current_date))
        #         result -= sum(x.amount for x in self.deposit_set.on_date(current_date))
        #         result -= sum(x.amount for x in self.income_transfers.on_date(current_date))
        #         result *= rule.credit_percent
        #         current_date += timedelta(days=1)
        #     return result


class OperationManager(models.Manager):
    def on_date_c(self, ts, cc, bk=False):
        print self.filter(date__gte=ts).count()
        if bk:
            return (super(OperationManager, self).get_queryset()).filter(date__gte=ts, cur_code=cc, account=bk)
        else:
            return (super(OperationManager, self).get_queryset()).filter(date__gte=ts, cur_code=cc)

    def on_date_out(self, date, act):
        return (super(OperationManager, self).get_queryset()).filter(date__gte=date, sender=act)

    def on_date_in(self, date, act):
        return (super(OperationManager, self).get_queryset()).filter(date__gte=date, receiver=act)


class Deposit(models.Model):
    REVERSED = 1
    PENDING = 2
    COMPLETED = 3
    # types
    CONVERSION = '4'
    PAYMENT = '1'
    INTERNATIONAL = '2'
    TOP_UP = '3'
    ##
    account = models.ForeignKey(BankAccount, related_name='deposit_set')
    amount = models.FloatField(default=0)
    banker = models.ForeignKey(UserProfile, null=True)
    date = models.DateTimeField(auto_now=True)
    cur_code = models.CharField(_('cur_code'), max_length=3, default='USD')
    tracking_code = models.IntegerField(default='0')
    type = models.CharField(default='0', choices=TYPE_CHOICES, max_length=2)
    commission = models.FloatField(default=0)
    status = models.IntegerField(default=COMPLETED)
    objects = OperationManager()

    def total_amount(self):
        return self.amount + self.commission

    def calculate_comission(self):
        thedate = self.date
        if type(self.date) is str:
            log.debug("Deposit object has a string date")
            thedate = datetime.strptime(self.date.__str__()[:11], '%Y-%m-%d').date()
        rule = Rule.on_date_s(thedate, self.cur_code)
        # print 'deposit comissiom,', rule.deposit_charge_percent
        # TODO check if comission less than 0.01
        self.commission = (rule.deposit_charge_percent * 0.01) * self.amount
        self.amount = self.amount - self.commission
        self.save()

        # def __str__(self):
        #     if self.account.owner.user.first_name or self.account.owner.user.last_name:
        #         return self.account.owner.user.first_name + " " + self.account.owner.user.last_name
        #     else:
        #         return self.account.id


class Withdraw(models.Model):
    CONVERSION = '4'
    PAYMENT = '1'
    WITHDRAWAL_REQUEST = '5'
    account = models.ForeignKey(BankAccount, related_name='withdraw_set')
    amount = models.FloatField()
    banker = models.ForeignKey(UserProfile, null=True)
    date = models.DateTimeField(default=datetime.now())
    type = models.CharField(default='0', choices=TYPE_CHOICES, max_length=2)
    cur_code = models.CharField(_('cur_code'), max_length=3, default='USD')
    objects = OperationManager()


class MoneyTransfer(models.Model):
    # Inter-bank-account money transfer
    # banker is same as sender
    # sender = models.ForeignKey(BankAccount, related_name='outcome_transfers')
    # receiver = models.ForeignKey(BankAccount, related_name='income_transfers')
    # date = models.DateTimeField(auto_now=True)
    # amount = models.FloatField()
    comment = models.CharField(max_length=255, default="")
    # cur_code = models.CharField(_('cur_code'), max_length=3, default='USD')
    deposit = models.OneToOneField(Deposit, related_name="payment_deposit")
    withdraw = models.OneToOneField(Withdraw, related_name="payment_withdraw")

    objects = OperationManager()


class CurrencyConversion(models.Model):
    deposit = models.OneToOneField(Deposit, related_name="conversion_deposit")
    withdraw = models.OneToOneField(Withdraw, related_name="conversion_withdraw")


class WithdrawalRequest(models.Model):
    src_account = models.ForeignKey(BankAccount, related_name="src_account", unique=False)
    dest_account = models.ForeignKey(BankAccount, related_name="dest_account", unique=False)
    status = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now=True)
    amount = models.IntegerField()

    #
    # class MerchantOrder(models.Model):
    #     number = models.CharField(max_length=20)
    #     deposit = models.ForeignKey(Deposit)


class CurrencyReserve(models.Model):
    currency = models.CharField(max_length=50, unique=True)
    recharge_date = models.DateTimeField(null=False, blank=False, default=datetime.now())
    on_recharge_amount = models.FloatField(null=False, blank=False, default=0)

    @property
    def reserve(self):
        temp_recharge_date = self.recharge_date
        result = self.on_recharge_amount
        conversion_deposits = []
        for item in CurrencyConversion.objects.filter(deposit__date__gte=temp_recharge_date,
                                                      deposit__cur_code=self.currency):
            conversion_deposits.append(item.deposit)

        result -= sum(x.amount for x in conversion_deposits)
        return result

    def save(self, *args, **kwargs):
        new_connection = settings.connect_to_redis()
        new_connection.set(self.currency, self.on_recharge_amount)
        super(CurrencyReserve, self).save(*args, **kwargs)

    def __str__(self):
        return self.currency
