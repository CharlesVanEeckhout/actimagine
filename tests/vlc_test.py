import sys
sys.path.append('..')

from package import io


def vlc_test(expected_results, tested_vlc):
    nb_bits = len(expected_results[0]["gb_buffer"])

    results = []
    gb_buffer = []
    for i in range(nb_bits):
        gb_buffer.append(0)
    i = 0
    while i < (1 << nb_bits):
        for j in range(nb_bits):
            gb_buffer[j] = (i >> (nb_bits-1-j)) & 1

        reader = io.DataReader()
        reader.set_data_bits(gb_buffer)
        code = reader.vlc2(tested_vlc)
        offset = int(reader.offset * 8)
        results.append({"gb_buffer": "".join([str(b) for b in gb_buffer]), "code": code, "end_index": offset})

        if code != -1:
            i = i | (((1 << nb_bits)-1) >> offset)
        i += 1

    for e_res, res in zip(expected_results, results, strict=True):
        if e_res["code"] != res["code"]:
            raise Exception("code " + str(res["code"]) + " is different from expected code " + str(e_res["code"]))
        # dont care what end_index is if code is -1, bc a code of -1 will crash the program anyway
        if e_res["code"] != -1 and e_res["end_index"] != res["end_index"]:
            raise Exception("end_index " + str(res["end_index"]) + " is different from expected end_index " + str(e_res["end_index"]))

