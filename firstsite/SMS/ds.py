import redis


class AuthCodeDataStructure:
    def __init__(self):
        pass

    data_store = redis.StrictRedis()
    phone_no = ""
    code = ""

    def set_code(self, phone_no, code):
        # create pin
        self.data_store.set(phone_no, code)
        self.data_store.expire(phone_no, 1800)  # 1800 seconds = 1/2 hour

    def get_code(self, phone_no):
        if self.data_store.exists(phone_no):
            return self.data_store.get(phone_no)
        else:
            return False
