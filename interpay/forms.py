from django.core.exceptions import ValidationError
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
            # print("error")
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


CURRENCY_CHOICES = {
    ('RLS', 'Rials'),
    ('USD', 'Dollar')
}


def validate_amount(value):
    if value < 1000:
        raise ValidationError(
            _('%(value) should be more than 1000'),
            params={'value': value},
        )


class RechargeAccountForm(forms.Form):
    #  we do not need this part right now since the only gateway which we use is Zarinpal
    # payment_gateway = forms.ChoiceField(widget=forms.RadioSelect)
    currency = forms.ChoiceField(choices=CURRENCY_CHOICES, required=True, label='')
    amount = forms.CharField(widget=forms.TextInput(attrs={'placeholder': '0.00'}))

    def __init__(self, *args, **kwargs):
        super(RechargeAccountForm, self).__init__(*args, **kwargs)
        self.fields['amount'].required = True
        self.fields['currency'].required = True

    class Meta:
        fields = ['currency', 'amount']

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount < 100:
            raise forms.ValidationError('Amount should be more than 100.')
        return amount


BANK_CHOICES = {
    ('Amin', 'Amin Investment Bank'),
    ('Ayandeh', 'Ayande Bank'),
    ('Day', 'Day Bank'),
    ('Maskan', 'Maskan Bank'),
    ('Mellat', 'Mellat Bank'),
    ('Melli', 'Bank Melli Iran'),
    ('Bank of Industry and Mine', 'Bank of Industry and Mine'),
    ('Pasargad', 'Bank Pasargad'),
    ('Saderat', 'Bank Saderat Iran'),
    ('Sepah', 'Bank Sepah'),
    ('Eghtesad-e-Novin', 'EN Bank'),
    ('Export Development Bank of Iran', 'Export Development Bank of Iran'),
    ('Ghavamin', 'Ghavamin Bank'),
    ('Persia', 'Imperial Bank of Persia'),
    ('Iran Zamin', 'Iran Zamin Bank'),
    ('Karafarin', 'Karafarin Bank'),
    ('Kardan', 'Kardan Investment Bank'),
    ('Keshavarzi', 'Keshavarzi Bank'),
    ('Mellat', 'Mellat Investment Bank'),
    ('Parsian', 'Parsian Bank'),
    ('Persia', 'Persia International Bank'),
    ('Post Bank', 'Post Bank of Iran'),
    ('Qarzol-Hasaneh Mehr', 'Qarzol-Hasaneh Mehr Iran Bank'),
    ('Refah', 'Refah Bank'),
    ('Saman', 'Saman Bank'),
    ('Sarmayeh', 'Sarmayeh Bank'),
    ('Sina', 'Sina Bank'),
    ('Tejarat', 'Tejarat Bank'),
}


class CreateBankAccountForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(CreateBankAccountForm, self).__init__(*args, **kwargs)
        self.fields['account_id'].widget = TextInput(attrs={
            'class': 'create_b_acc_form_field',
            'placeholder': 'Enter your account No.'})

    class Meta:
        model = BankAccount
        exclude = ['spectators', 'when_opened', 'owner', 'method']
        widgets = {
            'name': forms.Select(choices=BANK_CHOICES,
                                 attrs={'class': 'create_b_acc_form_field', 'id': 'bank_name', }),
            # TODO : these currency choices have to be customized and checked whether the related bank supports them.
            'cur_code': forms.Select(choices=CURRENCY_CHOICES,
                                     attrs={'class': 'create_b_acc_form_field'}), }
        # 'account_id': forms.TextInput(
        #     attrs={'class': 'create_b_acc_form_field', 'placeholder': 'Enter your account No.'})}




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
