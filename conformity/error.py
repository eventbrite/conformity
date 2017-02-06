class Error(object):
    def __init__(self, message, pointer=None):
        self.message = message
        self.pointer = pointer

    def __eq__(self, other):
        if not isinstance(other, Error):
            raise NotImplemented()
        return self.message == other.message and self.pointer == other.pointer

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        if self.pointer:
            return 'Error("{}", pointer="{}")'.format(self.message, self.pointer)
        return 'Error("{}")'.format(self.message)
