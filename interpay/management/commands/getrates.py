from currencies.models import Currency
from django.core.management.base import BaseCommand, CommandError
from django.http import HttpResponse
from currencies.utils import convert

from interpay.views import get_currency_rate


class Command(BaseCommand):
    help = 'obtains the latest rates from sarafi'

    def add_arguments(self, parser):
        parser.add_argument('poll_id', nargs='+', type=int)

    def handle(self, *args, **options):
        for poll_id in options['poll_id']:
            try:
                euro_rate = get_currency_rate("EUR")
                dollar_rate = get_currency_rate("USD")

                dollar_to_euro_ratio = float(dollar_rate) / (euro_rate * 1.00)
                dollar_to_euro_ratio = float("{0:.2f}".format(dollar_to_euro_ratio))
                dollar = Currency.objects.get(code='USD')
                dollar.factor = dollar_to_euro_ratio
                dollar.save()

                rial = Currency.objects.get(code='IRR')
                rial.factor = euro_rate
                rial.save()

                #poll = Poll.objects.get(pk=poll_id)
            except CommandError:
                raise CommandError('Currency "%s" does not exist' % poll_id)

            #poll.opened = False
            #poll.save()

            self.stdout.write(self.style.SUCCESS('Successfully obtained currency rates"%s"' % poll_id))