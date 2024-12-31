class DataReader:
    def __init__(self, data, offset):
        self.data = data
        self.offset = offset

    def bytes(self, length):
        if self.offset + length > len(self.data):
            raise Exception("tried to read out of bounds")
        self.offset += length
        return self.data[self.offset-length:self.offset]

    def int(self, length, byteorder="little", signed=False):
        return int.from_bytes(self.bytes(length), byteorder=byteorder, signed=signed)


class BitsReader:
    def __init__(self, data, offset):
        self.data = data
        self.offset = offset

    def bits(self, length):
        if self.offset + length > len(self.data):
            raise Exception("tried to read out of bounds")
        self.offset += length
        return self.data[self.offset-length:self.offset]

    def unsigned_expgolomb(self):
        bit_qty = 0
        bit_string = str(self.bits(1)[0])
        while bit_string[-1:] == "0":
            bit_qty += 1
            bit_string += str(self.bits(1)[0])
        for i in range(bit_qty):
            bit_string += str(self.bits(1)[0])
        return int(bit_string, 2) - 1

    def signed_expgolomb(self):
        ug = self.unsigned_expgolomb()
        if ug & 2 == 0:
            return ug // 2
        else:
            return -(ug // 2)
    
    def vlc2(self, vlc):
        bit_string = str(self.bits(1)[0])
        out = vlc.find_bit_string(bit_string)
        while len(out) > 0 and out[0][1] != bit_string:
            bit_string += str(self.bits(1)[0])
            out = vlc.find_bit_string(bit_string)
        if len(out) == 0:
            return -1
        return out[0][0]
