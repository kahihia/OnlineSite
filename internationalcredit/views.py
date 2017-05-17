from django.shortcuts import render
import stripe
from internationalcredit import settings
# Create your views here.
def home(request):
    if request.user.is_authenticated():
        return render(request, 'internationalcredit/payvisa.html', {'stripekey':settings.STRIPE_KEY})
    x = settings.STRIPE_KEY

    return render(request, 'internationalcredit/payvisa.html', {'stripekey':settings.STRIPE_KEY})


def callback(request):
    if request.method=="POST":
        stripe.api_key = "sk_test_1IYPvEcT4NtAM5zIFLkLLJRo"

        # Token is created using Stripe.js or Checkout!
        # Get the payment token submitted by the form:
        token = request.POST['stripeToken']  # Using Flask

        # Charge the user's card:
        charge = stripe.Charge.create(
            amount=request.POST.get("amount"),
            currency="gbp",
            description="Example charge",
            source=token,
        )
        m = charge.get("failure_message")


        emessage  = m + "payment successfully made"
        #charge.out

        return render(request, 'internationalcredit/payvisa.html', {'stripekey':settings.STRIPE_KEY, 'emessage': emessage})
    else:
        return render(request, 'internationalcredit/payvisa.html', {'stripekey':settings.STRIPE_KEY})


