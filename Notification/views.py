from models import Notification
from django.core.mail import send_mail


class NotificationClass():

    @staticmethod
    def make_notification(text, user, url):
        notification = Notification.objects.create(text=text, user=user, url=url)
        send_mail(
            'New Payment',
            text,
            'info@rizpal.com',
            [user.email],
            fail_silently=True,
        )
        return notification


