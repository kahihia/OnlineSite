from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, render_to_response
from django.views import View
from django.views.generic import TemplateView, CreateView
from interpay.forms import RegistrationForm, UserForm
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from interpay.models import UserProfile
from interpay.models import BankAccount

def main_page(request):
    if request.user.is_authenticated():
        return home(request)
    return render(request, 'index.html')


# class RegistrationView(CreateView):
#     template_name = '../templates/registeration_form.html'
#     user_form = UserForm
#     registration_form = RegistrationForm
#     model = UserProfile
#     registered = False
#
#     def post(self, request, *args, **kwargs):
#         print("post called")
#         user_form = UserForm(data=request.POST)
#         registration_form = RegistrationForm(data=request.POST)
#         return self.my_form_valid(user_form)
#
#     def my_form_valid(self, user_form, request):
#         print("is valid called")
#         user = user_form.save()
#         user.set_password(user.password)
#         user.save()
#
#         user_profile = self.registration_form.save(commit=False)
#         user_profile.email = user_form.cleaned_data['email']
#         user_profile.password = user.password
#
#         if user.is_active:
#             user_profile.is_active = True
#         user_profile.user = user
#
#         if 'picture' in request.FILES:
#             user_profile.picture = request.FILES['picture']
#         user_profile.save()
#         self.registered = True
#
#         new_user = authenticate(username=user_form.cleaned_data['username'],
#                                 password=user_form.cleaned_data['password'], )
#         login(request, new_user)
#
#     def get(self):
#         user_form = UserForm()
#         registration_form = RegistrationForm()


def register(request):
    registered = False
    if request.method == 'POST':
        user_form = UserForm(data=request.POST)
        registration_form = RegistrationForm(data=request.POST)

        if user_form.is_valid() and registration_form.is_valid():
            user = user_form.save()
            user.set_password(user.password)
            user.save()

            user_profile = registration_form.save(commit=False)
            user_profile.email = user_form.cleaned_data['email']
            # user_profile.date_of_birth = user_profile.cleaned_data['date_of_birth']
            user_profile.password = user.password
            print(user.is_active, "ine")
            if user.is_active:
                user_profile.is_active = True
            user_profile.user = user

            if 'picture' in request.FILES:
                user_profile.picture = request.FILES['picture']
            user_profile.save()
            registered = True

            new_user = authenticate(username=user_form.cleaned_data['username'],
                                    password=user_form.cleaned_data['password'], )
            login(request, new_user)

        else:
            print user_form.errors, registration_form.errors

    else:
        user_form = UserForm()
        registration_form = RegistrationForm()

    return render(request, 'registeration_form.html',
                  {'user_form': user_form, 'profile_form': registration_form, 'registered': registered})


def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)

        if user:
            if user.is_active:
                login(request, user, None)
                return HttpResponseRedirect('/home/')
            else:
                return HttpResponse("Your account is disabled.")
        else:
            print "Invalid login details: {0}, {1}".format(username, password)
            msg = "Username or Password is not valid. please try again."
            return render(request, 'index.html', {'msg': msg})

    else:
        return render(request, 'index.html', {})


@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect('/')


@login_required()
def home(request):
    return render(request, "home.html")


class HomeView(TemplateView):
    template_name = 'home.html'


@login_required()
def wallets(request):
    context = {
        'accountList': BankAccount.objects.filter(owner=request.user),
    }
    return render(request, "wallets.html", context)


@login_required()
def trans_history(request):
    return render(request, "trans_history.html")


@login_required()
def reports(request):
    return render(request, "reports.html")


@login_required()
def general(request):
    return render(request, "general.html")
