from django.contrib.auth.models import User
from interpay.models import *
user  = User.objects.get(username="test2@test.com")
up = UserProfile.objects.get(user=user)
#ba =BankAccount(name='usdaccount', owner=up, method=BankAccount.DEBIT, cur_code='USD')
#ba.save()
ba = BankAccount.objects.get(owner=up,cur_code='USD')
ba.delete()
d=Deposit(account=ba,amount=1000.00,banker=up, date=datetime.now, cur_code='USD')
d.save()
print ba.balance
