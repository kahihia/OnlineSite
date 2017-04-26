from django.contrib import admin
from interpay import models

# Register your models here.


class DepositAdmin(admin.ModelAdmin):
    list_display = ['id', 'type']


class WithdrawAdmin(admin.ModelAdmin):
    list_display = ['id', 'type']


class BankAccountAdmin(admin.ModelAdmin):
    list_display = ['id', 'account_id', 'owner', 'cur_code', 'method']


admin.site.register(models.UserProfile)
admin.site.register(models.CommonUser)
admin.site.register(models.Deposit, DepositAdmin)
admin.site.register(models.Withdraw, WithdrawAdmin)
admin.site.register(models.CurrencyReserve)
admin.site.register(models.MoneyTransfer)
admin.site.register(models.BankAccount, BankAccountAdmin)
admin.site.register(models.CurrencyConversion)
