from django.shortcuts import render
from django.contrib.auth import logout, login, authenticate
from interpay.models import WithdrawalRequest, MoneyTransfer
import requests


def home(request):
    if request.user.is_authenticated() and request.user.is_superuser:
        return render(request, 'manager/manager-home.html')
    elif request.method == 'GET':
        return render(request, 'manager/manager-login.html')
    elif not request.user.is_authenticated or not request.user.is_superuser:
        return render(request, 'manager/manager-login.html', {
            'error': 'Permission Denied.'
        })
    elif request.method == 'POST':
        gcapcha = request.POST['g-recaptcha-response']
        # post  https://www.google.com/recaptcha/api/siteverify
        post_data = {'secret': '6LfHKRMUAAAAAJG-cEV-SPcophf8jyXvrcghDtur', 'response': gcapcha}
        response = requests.post('https://www.google.com/recaptcha/api/siteverify', data=post_data)
        content = response.json()

        if not content['success']:
            return render(request, "manager/manager-login.html", {'error': 'Captcha is not entered.'})
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if (user is not None) and user.is_active and user.is_superuser:
            if not request.user.is_anonymous():
                logout(request)
            login(request, user)
            return render(request, 'manager/manager-home.html', {

            })


def withdrawal_requests(request):
    if request.method == "POST":
        withdrawal_id = request.POST['withdrawal_id']
        withdrawal = WithdrawalRequest.objects.get(id=withdrawal_id)
        src_account = withdrawal.src_account
        dest_account = withdrawal.dest_account
        withdrawals = WithdrawalRequest.objects.all()
        if src_account.balance < withdrawal.amount:
            return render(request, 'manager/manager-withdrawal-requests.html', {
                'withdrawal_requests': withdrawals,
                'error': 'Source account balance is not sufficient.',
                'withdraw_id': withdrawal_id
            })
        transfer = MoneyTransfer.objects.create(sender=src_account, receiver=dest_account, amount=withdrawal.amount,
                                                cur_code=src_account.cur_code)
        withdrawal.status = True
        withdrawal.save()
        withdrawals = WithdrawalRequest.objects.all()
        return render(request, 'manager/manager-withdrawal-requests.html', {
            'withdrawal_requests': withdrawals,
            'message': 'Transaction was successfully done.',
            'withdraw_id': withdrawal_id
        })
    withdrawals = WithdrawalRequest.objects.all()
    return render(request, 'manager/manager-withdrawal-requests.html', {
        'withdrawal_requests': withdrawals
    })
