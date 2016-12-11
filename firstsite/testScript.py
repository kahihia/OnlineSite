from django.contrib.auth.models import User
from interpay.models import *
user  = User.objects.get(username="test@rizpardakht.com")
#ba =BankAccount(name='usdaccount', owner=user, method=BankAccount.DEBIT, cur_code='IRR')
#ba.save()
ba = BankAccount.objects.get(owner=user,cur_code='USD')
#ba.delete()
d=Deposit(account=ba,total=1000.00,banker=user, when=ba.when_opened, cur_code='USD')
d.save()
print ba.balance
