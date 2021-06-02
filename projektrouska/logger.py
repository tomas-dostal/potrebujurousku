class Logger(object):

    def log(self, str):
        print("Log: {}".format(str))

    def error(self, str):
        print("Error: {}".format(str))

    def message(self, str):
        print("Message: {}".format(str))
