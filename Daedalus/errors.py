
class Error:
    def __init__(self, msg):
        self.msg = msg

class Result:
    def __init__(self, result):
        self.result = result

    def unpack(self):
        if type(self.result) == Error:
            return self.result.msg
        else:
            return self.result
            


