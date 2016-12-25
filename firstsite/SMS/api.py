import logging
import suds
from django.shortcuts import redirect



class ParsGreenSmsServiceClient:
    sendSmsURL = 'http://login.parsgreen.com/Api/SendSMS.asmx?WSDL'
    profileServiceURL = 'http://login.parsgreen.com/Api/profileservice.asmx?WSDL'
    msgServiceURL = 'http://login.parsgreen.com/Api/MsgService.asmx?WSDL'
    scheduleServiceURL = 'http://login.parsgreen.com/Api/ScheduleService.asmx?WSDL'

    def __init__(self):
        self.sendSmsClient = suds.client.Client(self.sendSmsURL)
        self.profileClient = suds.client.Client(self.profileServiceURL)
        # self.msgClient = suds.client.Client ( self.msgServiceURL )
        # on creating msg service client program crash
        self.scheduleClient = suds.client.Client(self.scheduleServiceURL)

        self.singnature = "664A4985-9989-457A-B21F-57C9C464AA4D"
        self.udh = ""
        self.success = 0x0
        self.retStr = []

    def sendSms(self, code, mobile_no):
        strArr = self.sendSmsClient.factory.create('ArrayOfString')
        strArr.string = [mobile_no]
        code = str(code) + " is your InterPay code."
        print "sending sms done"
        self.sendSmsClient.service.SendGroupSmsSimple("765822D8-383F-444F-A363-3EC951448412", "", strArr, code,
                                                      False, self.success)

    def getSendSmsClient(self):
        return self.sendSmsClient

    def getProfileClient(self):
        return self.profileClient

    def getMsgClient(self):
        return self.msgClient;

    # Sending text messages method
    def sendGroupSms(self, fromNo, toNoArr, txt, isFlash):
        strArr = self.sendSmsClient.factory.create('ArrayOfString')
        strArr.string = toNoArr
        self.retStr = self.sendSmsClient.service.SendGroupSMS(self.singnature, fromNo, strArr, txt, isFlash, self.udh,
                                                              self.success, self.retStr)
        return self.retStr.string

    # Get delivery method
    def getDelivery(self, recId):
        return self.sendSmsClient.service.GetDelivery(self.singnature, recId)

    # Get number of received text messages
    def getMsgCount(self, location, isRead):
        return self.msgClient.service.GetMsgCount(self.singnature, location, isRead)

    # Delete either received or sent text messages
    def deleteMsg(self, msgIdEncrypt):
        return self.msgClient.service.MsgDelete(self.singnature, msgIdEncrypt)

    # Change text message as unread/read
    def getMsgChangeIsRead(self, location, isRead):
        return self.msgClient.service.MsgChangeIsRead(self.singnature, location, isRead)

    # Get either received or sent text messages
    def getMessage(self, location, isRead):
        return self.msgClient.serivce.GetMessage(self.singnature, location, isRead)

    # Get credit amount left in your account
    def getCredit(self):
        return self.profileClient.service.GetCredit(self.singnature)

    # For transfer credit between from one account to another
    def transferCredit(self, toUserName, toPassWord, amount):
        return self.profileClient.service.TransferCredit(self.singnature, toUserName, toPassWord, amount)

    def regSchdeuleDaily(self, hour, minute, txt, toNoArr, fromNo, scheduleIdEncrypt):
        strArr = self.scheduleClient.factory.create('ArrayOfString')
        strArr.string = toNoArr
        return self.scheduleClient.service.RegSchdeuleDaily(self.singnature, hour, minute, txt, strArr, fromNo,
                                                            scheduleIdEncrypt)

    def regSchdeuleYearly(self, monthOfYearFa, dayOfMonthFa, hour, minute, txt, toNoArr, fromNo, scheduleIdEncrypt):
        strArr = self.scheduleClient.factory.create('ArrayOfString')
        strArr.string = toNoArr
        return self.scheduleClient.service.RegSchdeuleYearly(self.singnature, monthOfYearFa, dayOfMonthFa, hour, minute,
                                                             txt, strArr, fromNo, scheduleIdEncrypt)

    def deleteSchedule(self, scheduleIdEncrypt):
        return self.scheduleClient.service.DeleteSchedule(self.singnature, scheduleIdEncrypt)
