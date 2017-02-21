from __future__ import unicode_literals

from django.apps import AppConfig
from firstsite import settings


class InterpayConfig(AppConfig):
    name = 'interpay'
    verbose_name = "Interpay"

    def ready(self):
        settings.connect_to_redis()
        print "connect_to_redis initialized via interpay app"
