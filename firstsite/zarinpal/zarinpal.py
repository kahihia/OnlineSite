from django.http import HttpResponse
from django.shortcuts import redirect
from suds.client import Client

__url__ = 'reyhoonsoft.ir , rsdn.ir'
__license__ = "GPL 2.0 http://www.gnu.org/licenses/gpl-2.0.html"


class ZarinpalPaymentService:

    def __init__(self):
        pass

    MMERCHANT_ID = 'd5dd997c-595e-11e6-b573-000c295eb8fc'  # Required
    ZARINPAL_WEBSERVICE = 'https://www.zarinpal.com/pg/services/WebGate/wsdl'  # Required
    amount = 1000  # Amount will be based on Toman  Required
    description = "this is a test"
    email = 'farzane193@gmail.com'
    mobile = '09127273835'
    callBackUrl = '127.0.0.1:8000/home'

    def send_request(self):
        client = Client(self.ZARINPAL_WEBSERVICE)
        result = client.service.PaymentRequest(self.MMERCHANT_ID,
                                               self.amount,
                                               self.description,
                                               self.email,
                                               self.mobile,
                                               self.callBackUrl)
        print result.Status
        if result.Status == 100:
            return redirect('https://www.zarinpal.com/pg/StartPay/' + result.Authority)
        else:
            return 'Error'

    def verify(self, request):
        client = Client(self.ZARINPAL_WEBSERVICE)
        if request.args.get('Status') == 'OK':
            result = client.service.PaymentVerifition(self.MMERCHANT_ID,
                                                      request.args['Authority'],
                                                      self.amount)
            if result.Status == 100:
                return 'Transaction success. RefID: ' + str(result.RefID)
            elif result.Status == 101:
                return 'Transaction submitted : ' + str(result.Status)
            else:
                return 'Transaction failed. Status: ' + str(result.Status)
        else:
            return 'Transaction failed or canceled by user'


            # if __name__ == '__main__':
            #     app.run(debug=True)
