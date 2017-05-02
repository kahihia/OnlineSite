from models import Notification


class NotificationClass():
    @staticmethod
    def make_notification(text, user, url):
        notification = Notification.objects.create(text=text, user=user, url=url)
        return notification

