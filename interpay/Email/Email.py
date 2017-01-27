from interpay.models import User
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
import random
import string
import redis


class Email:
    destination_email = ""

    def __init__(self, email):
        self.destination_email = email

    def generate_token(self):
        new_token = ''.join(random.SystemRandom().choice(string.digits) for _ in range(30))
        new_connection = redis.StrictRedis(host='localhost', port=6379, db=0)
        user = User.objects.filter(email=self.destination_email)
        if user:
            user = user[0]
        data = {"user_id": user.id}
        new_connection.set(new_token, data)
        return new_token

    def send_email(self):
        if self.user_exists():
            new_token = self.generate_token()
            subject = "Password Retrieval"
            text_content = "Please click on the below link: "
            html_content = render_to_string('interpay/reset_password_email.html', {
                'token': new_token
            })
            mail = EmailMultiAlternatives(subject, text_content, 'info@rizpal.com', [self.destination_email])
            mail.attach_alternative(html_content, "text/html")
            code = mail.send()
            return code
        return 0

    def user_exists(self):
        user = User.objects.filter(email=self.destination_email)
        if user:
            return user[0]
        return False
