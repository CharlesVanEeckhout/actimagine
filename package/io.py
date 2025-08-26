import numpy as np


class DataReader:
    def __init__(self):
        self.data_size = 0
        self.data = None
        self.offset = 0

    def set_data_bytes(self, data, bitorder="little"):
        if bitorder == "big":
            for i in range(len(data)):
                data[i] = int((f"{data[i]:08b}")[::-1], 2)
        self.data_size = len(data)
        self.data = data

    def set_data_bits(self, data):
        self.data_size = len(data) / 8
        self.data = []
        data = np.concatenate([data, np.zeros((-len(data)) & 7)]) # complete the byte
        for i in range(0, len(data), 8):
            byte = 0
            byte_bits = data[i:i+8]
            for j in range(8):
                byte += int(byte_bits[j]) << j
            self.data.append(byte)

    def bit(self):
        if self.offset + 1/8 > self.data_size:
            raise Exception("tried to read out of bounds")
        bit_number = int(self.offset * 8) & 7
        bit = (self.data[int(self.offset)] >> bit_number) & 1
        self.offset += 1/8
        return bit

    def bits(self, bit_qty):
        bits = []
        for i in range(bit_qty):
            bits.append(self.bit())
        return bits

    def byte(self):
        if self.offset + 1 > self.data_size:
            raise Exception("tried to read out of bounds")
        self.offset += 1
        if self.offset % 1 == 0:
            return self.data[self.offset-1]
        bit_number = int(self.offset * 8) & 7
        byte = (((self.data[int(self.offset)] << 8) + self.data[int(self.offset-1)]) >> bit_number) & 0xff
        return byte

    def bytes(self, byte_qty):
        bytes = []
        for i in range(byte_qty):
            bytes.append(self.byte())
        return bytes

    def int_from_bits(self, bit_qty, bitorder="little", signed=False):
        bits = self.bits(bit_qty)
        if bitorder == "little":
            bits.reverse()
        value = 0
        for i in range(len(bits)):
            value += bits[i] << i
        value_max = 1 << bit_qty
        if signed and value < 0:
            value += value_max
        if value < 0 or value >= value_max:
            raise Exception("value is out of bounds")
        return value

    def int_from_bytes(self, byte_qty, byteorder="little", signed=False):
        return int.from_bytes(self.bytes(byte_qty), byteorder=byteorder, signed=signed)

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


class BitStreamWriter:
    # byte order of words is little endian
    # bit order per word is msb to lsb
    def __init__(self):
        self.data = []
        self.bit_number = 15

    def get_data_bytes(self):
        bytes = []
        for word in self.data:
            bytes.append(word & 0xff)
            bytes.append(word >> 8)
        return bytes

    def bit(self, value):
        if self.bit_number == 15:
            self.data.append(value << 15)
        else:
            self.data[len(self.data)-1] += value << self.bit_number
        self.bit_number = (self.bit_number - 1) & 15

    def bits(self, data):
        for bit in data:
            self.bit(bit)

    def byte(self, value):
        value = int((f"{value:08b}")[::-1], 2)
        if self.bit_number == 15:
            self.data.append(value << 8)
        elif self.bit_number >= 7:
            self.data[len(self.data)-1] += (value << (self.bit_number - 7))
        else:
            self.data[len(self.data)-1] += (value >> (7 - self.bit_number))
            self.data.append((value << (self.bit_number + 9)) & 0xffff)

    def bytes(self, data):
        for byte in data:
            self.byte(byte)

    def int_to_bytes(self, value, length, byteorder="little"):
        self.bytes(list(value.to_bytes(length, byteorder)))

    def int_to_bits(self, value, length, bitorder="little", signed=False):
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

