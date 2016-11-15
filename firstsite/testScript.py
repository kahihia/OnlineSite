from django.contrib.auth.models import User
from interpay.models import *
user  = User.objects.get(username="test@rizpardakht.com")
#//ba =BankAccount(name='salmantest', owner=user, method=BankAccount.DEBIT)
#//ba.save()
ba = BankAccount.objects.get(owner=user)
d=Deposit(account=ba,total=101.00,banker=user, when=ba.when_opened, cur_code='GBP')
print ba.balance
