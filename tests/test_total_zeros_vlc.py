import sys
sys.path.append('..')

from package import vlc
from vlc_test import vlc_test


def test_total_zeros_vlc_1():
    expected_results = [
        {"gb_buffer": "000000000", "code": -1, "end_index": 0},
        {"gb_buffer": "000000001", "code": 15, "end_index": 9},
        {"gb_buffer": "000000010", "code": 14, "end_index": 9},
        {"gb_buffer": "000000011", "code": 13, "end_index": 9},
        {"gb_buffer": "000000100", "code": 12, "end_index": 8},
        {"gb_buffer": "000000110", "code": 11, "end_index": 8},
        {"gb_buffer": "000001000", "code": 10, "end_index": 7},
        {"gb_buffer": "000001100", "code": 9, "end_index": 7},
        {"gb_buffer": "000010000", "code": 8, "end_index": 6},
        {"gb_buffer": "000011000", "code": 7, "end_index": 6},
        {"gb_buffer": "000100000", "code": 6, "end_index": 5},
        {"gb_buffer": "000110000", "code": 5, "end_index": 5},
        {"gb_buffer": "001000000", "code": 4, "end_index": 4},
        {"gb_buffer": "001100000", "code": 3, "end_index": 4},
        {"gb_buffer": "010000000", "code": 2, "end_index": 3},
        {"gb_buffer": "011000000", "code": 1, "end_index": 3},
        {"gb_buffer": "100000000", "code": 0, "end_index": 1},
    ]
    
    vlc_test(expected_results, vlc.total_zeros_vlc[1])


def test_total_zeros_vlc_2():
    expected_results = [
        {"gb_buffer": "000000000", "code": 14, "end_index": 6},
        {"gb_buffer": "000001000", "code": 13, "end_index": 6},
        {"gb_buffer": "000010000", "code": 12, "end_index": 6},
        {"gb_buffer": "000011000", "code": 11, "end_index": 6},
        {"gb_buffer": "000100000", "code": 10, "end_index": 5},
        {"gb_buffer": "000110000", "code": 9, "end_index": 5},
        {"gb_buffer": "001000000", "code": 8, "end_index": 4},
        {"gb_buffer": "001100000", "code": 7, "end_index": 4},
        {"gb_buffer": "010000000", "code": 6, "end_index": 4},
        {"gb_buffer": "010100000", "code": 5, "end_index": 4},
        {"gb_buffer": "011000000", "code": 4, "end_index": 3},
        {"gb_buffer": "100000000", "code": 3, "end_index": 3},
        {"gb_buffer": "101000000", "code": 2, "end_index": 3},
        {"gb_buffer": "110000000", "code": 1, "end_index": 3},
        {"gb_buffer": "111000000", "code": 0, "end_index": 3},
    ]
    
    vlc_test(expected_results, vlc.total_zeros_vlc[2])


def test_total_zeros_vlc_3():
    expected_results = [
        {"gb_buffer": "000000000", "code": 13, "end_index": 6},
        {"gb_buffer": "000001000", "code": 11, "end_index": 6},
        {"gb_buffer": "000010000", "code": 12, "end_index": 5},
        {"gb_buffer": "000100000", "code": 10, "end_index": 5},
        {"gb_buffer": "000110000", "code": 9, "end_index": 5},
        {"gb_buffer": "001000000", "code": 8, "end_index": 4},
        {"gb_buffer": "001100000", "code": 5, "end_index": 4},
        {"gb_buffer": "010000000", "code": 4, "end_index": 4},
        {"gb_buffer": "010100000", "code": 0, "end_index": 4},
        {"gb_buffer": "011000000", "code": 7, "end_index": 3},
        {"gb_buffer": "100000000", "code": 6, "end_index": 3},
        {"gb_buffer": "101000000", "code": 3, "end_index": 3},
        {"gb_buffer": "110000000", "code": 2, "end_index": 3},
        {"gb_buffer": "111000000", "code": 1, "end_index": 3},
    ]
    
    vlc_test(expected_results, vlc.total_zeros_vlc[3])


def test_total_zeros_vlc_4():
    expected_results = [
        {"gb_buffer": "000000000", "code": 12, "end_index": 5},
        {"gb_buffer": "000010000", "code": 11, "end_index": 5},
        {"gb_buffer": "000100000", "code": 10, "end_index": 5},
        {"gb_buffer": "000110000", "code": 0, "end_index": 5},
        {"gb_buffer": "001000000", "code": 9, "end_index": 4},
        {"gb_buffer": "001100000", "code": 7, "end_index": 4},
        {"gb_buffer": "010000000", "code": 3, "end_index": 4},
        {"gb_buffer": "010100000", "code": 2, "end_index": 4},
        {"gb_buffer": "011000000", "code": 8, "end_index": 3},
        {"gb_buffer": "100000000", "code": 6, "end_index": 3},
        {"gb_buffer": "101000000", "code": 5, "end_index": 3},
        {"gb_buffer": "110000000", "code": 4, "end_index": 3},
        {"gb_buffer": "111000000", "code": 1, "end_index": 3},
    ]
    
    vlc_test(expected_results, vlc.total_zeros_vlc[4])


def test_total_zeros_vlc_5():
    expected_results = [
        {"gb_buffer": "000000000", "code": 11, "end_index": 5},
        {"gb_buffer": "000010000", "code": 9, "end_index": 5},
        {"gb_buffer": "000100000", "code": 10, "end_index": 4},
        {"gb_buffer": "001000000", "code": 8, "end_index": 4},
        {"gb_buffer": "001100000", "code": 2, "end_index": 4},
        {"gb_buffer": "010000000", "code": 1, "end_index": 4},
        {"gb_buffer": "010100000", "code": 0, "end_index": 4},
        {"gb_buffer": "011000000", "code": 7, "end_index": 3},
        {"gb_buffer": "100000000", "code": 6, "end_index": 3},
        {"gb_buffer": "101000000", "code": 5, "end_index": 3},
        {"gb_buffer": "110000000", "code": 4, "end_index": 3},
        {"gb_buffer": "111000000", "code": 3, "end_index": 3},
    ]
    
    vlc_test(expected_results, vlc.total_zeros_vlc[5])


def test_total_zeros_vlc_6():
    expected_results = [
        {"gb_buffer": "000000000", "code": 10, "end_index": 6},
        {"gb_buffer": "000001000", "code": 0, "end_index": 6},
        {"gb_buffer": "000010000", "code": 1, "end_index": 5},
        {"gb_buffer": "000100000", "code": 8, "end_index": 4},
        {"gb_buffer": "001000000", "code": 9, "end_index": 3},
        {"gb_buffer": "010000000", "code": 7, "end_index": 3},
        {"gb_buffer": "011000000", "code": 6, "end_index": 3},
        {"gb_buffer": "100000000", "code": 5, "end_index": 3},
        {"gb_buffer": "101000000", "code": 4, "end_index": 3},
        {"gb_buffer": "110000000", "code": 3, "end_index": 3},
        {"gb_buffer": "111000000", "code": 2, "end_index": 3},
    ]
    
    vlc_test(expected_results, vlc.total_zeros_vlc[6])


def test_total_zeros_vlc_7():
    expected_results = [
        {"gb_buffer": "000000000", "code": 9, "end_index": 6},
        {"gb_buffer": "000001000", "code": 0, "end_index": 6},
        {"gb_buffer": "000010000", "code": 1, "end_index": 5},
        {"gb_buffer": "000100000", "code": 7, "end_index": 4},
        {"gb_buffer": "001000000", "code": 8, "end_index": 3},
        {"gb_buffer": "010000000", "code": 6, "end_index": 3},
        {"gb_buffer": "011000000", "code": 4, "end_index": 3},
        {"gb_buffer": "100000000", "code": 3, "end_index": 3},
        {"gb_buffer": "101000000", "code": 2, "end_index": 3},
        {"gb_buffer": "110000000", "code": 5, "end_index": 2},
    ]
    
    vlc_test(expected_results, vlc.total_zeros_vlc[7])


def test_total_zeros_vlc_8():
    expected_results = [
        {"gb_buffer": "000000000", "code": 8, "end_index": 6},
        {"gb_buffer": "000001000", "code": 0, "end_index": 6},
        {"gb_buffer": "000010000", "code": 2, "end_index": 5},
        {"gb_buffer": "000100000", "code": 1, "end_index": 4},
        {"gb_buffer": "001000000", "code": 7, "end_index": 3},
        {"gb_buffer": "010000000", "code": 6, "end_index": 3},
        {"gb_buffer": "011000000", "code": 3, "end_index": 3},
        {"gb_buffer": "100000000", "code": 5, "end_index": 2},
        {"gb_buffer": "110000000", "code": 4, "end_index": 2},
    ]
    
    vlc_test(expected_results, vlc.total_zeros_vlc[8])


def test_total_zeros_vlc_9():
    expected_results = [
        {"gb_buffer": "000000000", "code": 1, "end_index": 6},
        {"gb_buffer": "000001000", "code": 0, "end_index": 6},
        {"gb_buffer": "000010000", "code": 7, "end_index": 5},
        {"gb_buffer": "000100000", "code": 2, "end_index": 4},
        {"gb_buffer": "001000000", "code": 5, "end_index": 3},
        {"gb_buffer": "010000000", "code": 6, "end_index": 2},
        {"gb_buffer": "100000000", "code": 4, "end_index": 2},
        {"gb_buffer": "110000000", "code": 3, "end_index": 2},
    ]
    
    vlc_test(expected_results, vlc.total_zeros_vlc[9])


def test_total_zeros_vlc_10():
    expected_results = [
        {"gb_buffer": "000000000", "code": 1, "end_index": 5},
        {"gb_buffer": "000010000", "code": 0, "end_index": 5},
        {"gb_buffer": "000100000", "code": 6, "end_index": 4},
        {"gb_buffer": "001000000", "code": 2, "end_index": 3},
        {"gb_buffer": "010000000", "code": 5, "end_index": 2},
        {"gb_buffer": "100000000", "code": 4, "end_index": 2},
        {"gb_buffer": "110000000", "code": 3, "end_index": 2},
    ]
    
    vlc_test(expected_results, vlc.total_zeros_vlc[10])


def test_total_zeros_vlc_11():
    expected_results = [
        {"gb_buffer": "000000000", "code": 0, "end_index": 4},
        {"gb_buffer": "000100000", "code": 1, "end_index": 4},
        {"gb_buffer": "001000000", "code": 2, "end_index": 3},
        {"gb_buffer": "010000000", "code": 3, "end_index": 3},
        {"gb_buffer": "011000000", "code": 5, "end_index": 3},
        {"gb_buffer": "100000000", "code": 4, "end_index": 1},
    ]
    
    vlc_test(expected_results, vlc.total_zeros_vlc[11])


def test_total_zeros_vlc_12():
    expected_results = [
        {"gb_buffer": "000000000", "code": 0, "end_index": 4},
        {"gb_buffer": "000100000", "code": 1, "end_index": 4},
        {"gb_buffer": "001000000", "code": 4, "end_index": 3},
        {"gb_buffer": "010000000", "code": 2, "end_index": 2},
        {"gb_buffer": "100000000", "code": 3, "end_index": 1},
    ]
    
    vlc_test(expected_results, vlc.total_zeros_vlc[12])


def test_total_zeros_vlc_13():
    expected_results = [
        {"gb_buffer": "000000000", "code": 0, "end_index": 3},
        {"gb_buffer": "001000000", "code": 1, "end_index": 3},
        {"gb_buffer": "010000000", "code": 3, "end_index": 2},
        {"gb_buffer": "100000000", "code": 2, "end_index": 1},
    ]
    
    vlc_test(expected_results, vlc.total_zeros_vlc[13])


def test_total_zeros_vlc_14():
    expected_results = [
        {"gb_buffer": "000000000", "code": 0, "end_index": 2},
        {"gb_buffer": "010000000", "code": 1, "end_index": 2},
        {"gb_buffer": "100000000", "code": 2, "end_index": 1},
    ]
    
    vlc_test(expected_results, vlc.total_zeros_vlc[14])


def test_total_zeros_vlc_15():
    expected_results = [
        {"gb_buffer": "000000000", "code": 0, "end_index": 1},
        {"gb_buffer": "100000000", "code": 1, "end_index": 1},
    ]
    
    vlc_test(expected_results, vlc.total_zeros_vlc[15])

