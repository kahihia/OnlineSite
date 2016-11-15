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
        exclude = ['user', 'email', 'password', 'is_active', 'date_joined', 'picture']
        widgets = {
            'national_code': forms.TextInput(
                attrs={'class': 'registration-form-field', 'placeholder': 'National Code', 'id': 'national_code', }),
            'country': forms.Select(attrs={'class': 'registration-form-field', 'placeholder': 'Country'}),
        }

        # def __init__(self, *args, **kwargs):
        #     super(RegistrationForm, self).__init__(*args, **kwargs)
        #     self.fields['username'].widget.attrs.update({'class': 'registeration-form-field'})
