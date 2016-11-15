from django.shortcuts import render
from django.http import HttpResponse
from interpay.models import User

def index(request):
    return render(request, 'conversion/index.html')
# Create your views here
def detail(request, trans_id):
    p = User.objects.get(first_name = "salman")
    b = models.BankAccount.objects.get(owner  = p)
    c = models.BankAccount.objects.all()
    return HttpResponse("You're looking at transaction %s balance." % b.balance)

