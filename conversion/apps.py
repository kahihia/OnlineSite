from __future__ import unicode_literals

from django.apps import AppConfig
from firstsite import settings


class ConversionConfig(AppConfig):
    name = 'conversion'
    verbose_name = "Conversion"

    def ready(self):
        #settings.connect_to_redis()
        print "connect_to_redis initialized via conversion app"
