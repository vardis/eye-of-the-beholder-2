import struct


class BinaryReader:
    """

    """

    def __init__(self, filename):

        self.filename = filename
        self.handle = None

    def __enter__(self):
        """

        :return:
        """
        self.handle = open(self.filename, 'rb')

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """

        :param exc_type:
        :param exc_val:
        :param exc_tb:
        :return:
        """
        if self.handle:
            self.handle.close()
            self.handle = None

    @property
    def offset(self):
        """

        :return:
        """
        if not self.handle:
            return None

        return self.handle.tell()

    @property
    def offset_hex(self):
        """

        :return:
        """
        return hex(self.offset)

    def read_ubyte(self, count=1):
        """

        :param count:
        :return:
        """
        val = struct.unpack('{count}B'.format(count=count), self.handle.read(count))

        if count == 1:
            return val[0]
        return val

    def read_byte(self, count=1):
        """

        :param count:
        :return:
        """
        val = struct.unpack('{count}b'.format(count=count), self.handle.read(count))
        if count == 1:
            return val[0]
        return val

    def peek_ubyte(self, count=1):
        """

        :param count:
        :return:
        """
        s = struct.unpack('{count}B'.format(count=count), self.handle.read(count))
        self.handle.seek(-count, 1)
        if count == 1:
            return s[0]

        return list(s[:count])

    def peek_byte(self, count=1):
        """

        :param count:
        :return:
        """
        value = struct.unpack('{count}b'.format(count=count), self.handle.read(count))[0]
        self.handle.seek(-count, 1)
        return value

    def read_ushort(self, count=1):
        """

        :param count:
        :return:
        """
        val = struct.unpack('{count}H'.format(count=count), self.handle.read(count * 2))
        if count == 1:
            return val[0]
        return val

    def read_short(self, count=1):
        """

        :param count:
        :return:
        """
        val = struct.unpack('{count}h'.format(count=count), self.handle.read(count * 2))
        if count == 1:
            return val[0]
        return val

    def peek_ushort(self, count=1):
        """

        :param count:
        :return:
        """
        value = struct.unpack('{count}H'.format(count=count), self.handle.read(count * 2))[0]
        self.handle.seek(-count * 2, 1)
        return value

    def peek_short(self, count=1):
        """

        :param count:
        :return:
        """
        value = struct.unpack('{count}h'.format(count=count), self.handle.read(count * 2))[0]
        self.handle.seek(-count * 2, 1)
        return value

    def read_uint(self, count=1):
        """

        :param count:
        :return:
        """
        val = struct.unpack('{count}I'.format(count=count), self.handle.read(count * 4))
        if count == 1:
            return val[0]
        return val

    def read_int(self, count=1):
        """

        :param count:
        :return:
        """
        val = struct.unpack('{count}i'.format(count=count), self.handle.read(count * 4))[0]
        if count == 1:
            return val[0]
        return val

    def read_string(self, length=0):
        """

        :param length:
        :return:
        """

        buff = struct.unpack('{length}s'.format(length=length), self.handle.read(length))[0]

        string = ''
        for c in buff:
            if c == 0:
                break
            string += chr(c)

        return string

    def peek_string(self, length=0):
        str = self.read_string(length)
        self.rewind(length)
        return str

    def search_string(self):
        """

        :return:
        """

        string = ''

        while True:
            b = self.read_ubyte()

            if b == 0x0:
                return string

            string += chr(b)

    def rewind(self, offset):
        """
        Move offset backward
        :param offset:
        :return:
        """

        self.handle.seek(-offset, 1)

    def seek(self, offset):
        """
        Set offset
        :param offset:
        :return:
        """

        self.handle.seek(offset)
