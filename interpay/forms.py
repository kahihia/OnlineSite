from django.core.mail import send_mail
from django.forms import TextInput, SelectDateWidget
from django.template import Context, Template
from firstsite.settings import MEDIA_ROOT
from interpay.models import *
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.core.validators import validate_email


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'password')
        email = {
            'required': True
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'registration-form-field', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'registration-form-field', 'placeholder': 'Last Name'}),
            'username': forms.TextInput(attrs={'class': 'registration-form-field', 'placeholder': 'Username'}),
            'email': forms.TextInput(attrs={'class': 'registration-form-field', 'placeholder': 'Email'}),
            'password': forms.TextInput(attrs={'class': 'registration-form-field'}),
        }

    password = forms.CharField(required=True, widget=forms.PasswordInput(
        attrs={'class': 'registration-form-field', 'placeholder': 'Password'}))
    confirm_password = forms.CharField(required=True,
                                       widget=forms.PasswordInput(attrs={'class': 'registration-form-field',
                                                                         'placeholder': 'Re-type your password'}))

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)

        self.fields['email'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True

    def clean_email(self):
        email = self.cleaned_data.get('email')
        username = self.cleaned_data.get('username')
        if not email:
            raise forms.ValidationError('Email')
        if email and User.objects.filter(email=email).count() > 0:
            raise forms.ValidationError('This Email is registered before.')
        return email

    def clean_confirm_password(self):
        password = self.cleaned_data.get('password', '')
        confirm_password = self.cleaned_data.get("confirm_password", '')
        if password != confirm_password:
            print("error")
            raise forms.ValidationError("Passwords do not match!")
        return confirm_password

        # def send_email(self, datas):
        #     link = "http://127.0.0.1:8000//activate/" + datas['activation_key']
        #     c = Context({'activation_link': link, 'username': datas['username']})
        #     f = open(MEDIA_ROOT + datas['email_path'], 'r')
        #     t = Template(f.read())
        #     f.close()
        #     message = t.render(c)
        #     # print unicode(message).encode('utf8')
        #     send_mail(datas['email_subject'], message, 'yourdomain <no-reply@yourdomain.com>', [datas['email']],
        #               fail_silently=False)


class RegistrationForm(forms.ModelForm):
    date_of_birth = forms.DateField(widget=SelectDateWidget(years=range(1920, 2013)))

    class Meta:
        model = UserProfile
        exclude = ['user', 'password', 'email', 'is_active', 'date_joined', 'picture']
        widgets = {
            'national_code': forms.TextInput(
                attrs={'class': 'registration-form-field', 'placeholder': 'National Code', 'id': 'national_code', }),
            'country': forms.Select(attrs={'class': 'registration-form-field', 'placeholder': 'Country'}),
            'mobile_number': forms.TextInput(
                attrs={'name': 'mobile_no', 'class': 'registration-form-field',
                       'placeholder': 'Mobile (Example: 09121234567)',
                       'id': 'mob_no'}),
        }

    def clean_national_code(self):
        national_code = self.cleaned_data['national_code']
        if not national_code:
            raise forms.ValidationError('National Code is mandatory')
        if not check_id(national_code):
            raise forms.ValidationError("Please enter a valid National Code.")
        # if national_code and UserProfile.objects.filter(national_code=national_code).count() > 0:
        #     raise forms.ValidationError("This National Code is registered before.")

        return national_code


# national code verification
def check_id(id):
    is_valid = False
    checksum = 0
    id = int(id)
    first_digit = id % 10
    id /= 10
    for x in range(2, 11):
        digit = id % 10
        id /= 10
        checksum += x * digit
    remainder = checksum % 11
    if (remainder < 2) & (first_digit == remainder):
        is_valid = True
    if (remainder >= 2) & (first_digit == (11 - remainder)):
        is_valid = True
    return is_valid


class AuthenticationForm(forms.Form):
    code = forms.TextInput()

    def __init__(self, *args, **kwargs):
        super(AuthenticationForm, self).__init__(*args, **kwargs)
        self.fields['code'].required = True

    class Meta:
        widgets = {
            'code': forms.TextInput(
                attrs={'id': 'verification-code', 'class': 'registration-form-field', 'placeholder': 'Enter the code',
                       'type': 'text', 'maxlength': '6'})}

    def clean_authentication_code(self):
        authentication_code = self.cleaned_data.get('code', '')
        if not authentication_code:
            raise forms.ValidationError('Please enter the code which was sent to you.')
        return authentication_code

        # def verify_code(code):
        #     is_valid = False
        #
        # def send_email(self, datas):
        #     link = "http://127.0.0.1:8000//activate/" + datas['activation_key']
        #     c = Context({'activation_link': link, 'username': datas['username']})
        #     f = open(MEDIA_ROOT + datas['email_path'], 'r')
        #     t = Template(f.read())
        #     f.close()
        #     message = t.render(c)
        #     # print unicode(message).encode('utf8')
        #     send_mail(datas['email_subject'], message, 'yourdomain <no-reply@yourdomain.com>', [datas['email']],
        #               fail_silently=False)
