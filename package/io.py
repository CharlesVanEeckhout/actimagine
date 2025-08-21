import numpy as np


class BytesReader:
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

    def bit(self):
        if self.offset + 1 > len(self.data):
            raise Exception("tried to read out of bounds")
        self.offset += 1
        return self.data[self.offset-1]

    def bits(self, length):
        if self.offset + length > len(self.data):
            raise Exception("tried to read out of bounds")
        self.offset += length
        return self.data[self.offset-length:self.offset]

    def int(self, length, bitorder="little", signed=False):
        bits = self.bits(length)
        if bitorder == "big":
            bits.reverse()
        
        out = 0
        for bit in bits:
            out = out*2 + bit
        return out

    def unsigned_expgolomb(self):
        bit_qty = 0
        bit_string = str(self.bit())
        while bit_string[-1:] == "0":
            bit_qty += 1
            bit_string += str(self.bit())
        for i in range(bit_qty):
            bit_string += str(self.bit())
        return int(bit_string, 2) - 1

    def signed_expgolomb(self):
        ug = self.unsigned_expgolomb() + 1
        if ug & 1 == 0:
            return ug // 2
        else:
            return -(ug // 2)

    def vlc2(self, vlc):
        bit_string = str(self.bit())
        out = vlc.find_bit_string(bit_string)
        while len(out) > 0 and out[0][1] != bit_string:
            bit_string += str(self.bit())
            out = vlc.find_bit_string(bit_string)
        if len(out) == 0:
            return -1
        return out[0][0]


class BytesWriter:
    def __init__(self):
        self.data = []

    def bytes(self, data):
        self.data += data

    def int(self, value, length, byteorder="little"):
        self.data += list(value.to_bytes(length, byteorder))


class BitsWriter:
    def __init__(self):
        self.data = []

    def bit(self, value):
        self.data.append(value)

    def bits(self, data):
        self.data += data

    def int(self, value, length, bitorder="little", signed=False):
        value_max = 1 << length
        if signed and value < 0:
            value += value_max
        if value < 0 or value >= value_max:
            raise Exception("value is out of bounds")
        
        out = []
        for i in range(length):
            out.append(value & 1)
            value = value // 2
        if bitorder == "little":
            out.reverse()
        self.bits(out)

    def unsigned_expgolomb(self, value):
        if value < 0:
            raise Exception("value is out of bounds")
        value += 1
        out = f"{value:b}"
        out = "0" * (len(out) - 1) + out
        self.bits([int(bit) for bit in out])

    def signed_expgolomb(self, value):
        value = value * 2
        if value <= 0:
            value = 1 - value
        self.unsigned_expgolomb(value - 1)

    def vlc2(self, value, vlc):
        if value < 0 or value >= len(vlc.bit_strings):
            raise Exception("value is out of bounds")
        bs = vlc.bit_strings[value]
        for b in bs:
            self.bit(int(b))

