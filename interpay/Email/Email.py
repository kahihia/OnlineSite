from interpay.models import User
from django.core.mail import send_mail


class Email:
    destination_email = ""

    def __init__(self, email):
        self.destination_email = email

    def send_email(self):
        if self.user_exists():
            user = self.user_exists()
            password = User.objects.make_random_password()
            user.set_password(password)
            send_mail(
                'Password Retrieval',
                'Your new password is: ' + password,
                '',
                [self.destination_email],
                fail_silently=False,
            )
            return 1
        return 0

    def user_exists(self):
        user = User.objects.filter(email=self.destination_email)
        if user:
            return user[0]
        return False
