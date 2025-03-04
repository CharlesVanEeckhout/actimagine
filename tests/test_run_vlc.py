import sys
sys.path.append('..')

import vlc
from vlc_test import vlc_test


def test_run_vlc_1():
    expected_results = [
        {"gb_buffer": "000", "code": 1, "end_index": 1},
        {"gb_buffer": "100", "code": 0, "end_index": 1},
    ]
    
    vlc_test(expected_results, vlc.run_vlc[1])

def test_run_vlc_2():
    expected_results = [
        {"gb_buffer": "000", "code": 2, "end_index": 2},
        {"gb_buffer": "010", "code": 1, "end_index": 2},
        {"gb_buffer": "100", "code": 0, "end_index": 1},
    ]
    
    vlc_test(expected_results, vlc.run_vlc[2])

def test_run_vlc_3():
    expected_results = [
        {"gb_buffer": "000", "code": 3, "end_index": 2},
        {"gb_buffer": "010", "code": 2, "end_index": 2},
        {"gb_buffer": "100", "code": 1, "end_index": 2},
        {"gb_buffer": "110", "code": 0, "end_index": 2},
    ]
    
    vlc_test(expected_results, vlc.run_vlc[3])

def test_run_vlc_4():
    expected_results = [
        {"gb_buffer": "000", "code": 4, "end_index": 3},
        {"gb_buffer": "001", "code": 3, "end_index": 3},
        {"gb_buffer": "010", "code": 2, "end_index": 2},
        {"gb_buffer": "100", "code": 1, "end_index": 2},
        {"gb_buffer": "110", "code": 0, "end_index": 2},
    ]
    
    vlc_test(expected_results, vlc.run_vlc[4])

def test_run_vlc_5():
    expected_results = [
        {"gb_buffer": "000", "code": 5, "end_index": 3},
        {"gb_buffer": "001", "code": 4, "end_index": 3},
        {"gb_buffer": "010", "code": 3, "end_index": 3},
        {"gb_buffer": "011", "code": 2, "end_index": 3},
        {"gb_buffer": "100", "code": 1, "end_index": 2},
        {"gb_buffer": "110", "code": 0, "end_index": 2},
    ]
    
    vlc_test(expected_results, vlc.run_vlc[5])

def test_run_vlc_6():
    expected_results = [
        {"gb_buffer": "000", "code": 1, "end_index": 3},
        {"gb_buffer": "001", "code": 2, "end_index": 3},
        {"gb_buffer": "010", "code": 4, "end_index": 3},
        {"gb_buffer": "011", "code": 3, "end_index": 3},
        {"gb_buffer": "100", "code": 6, "end_index": 3},
        {"gb_buffer": "101", "code": 5, "end_index": 3},
        {"gb_buffer": "110", "code": 0, "end_index": 2},
    ]
    
    vlc_test(expected_results, vlc.run_vlc[6])

def test_run7_vlc():
    expected_results = [
        {"gb_buffer": "000000000000", "code": -1, "end_index": 6},
        {"gb_buffer": "000000000001", "code": -1, "end_index": 6},
        {"gb_buffer": "000000000010", "code": 14, "end_index": 11},
        {"gb_buffer": "000000000100", "code": 13, "end_index": 10},
        {"gb_buffer": "000000001000", "code": 12, "end_index": 9},
        {"gb_buffer": "000000010000", "code": 11, "end_index": 8},
        {"gb_buffer": "000000100000", "code": 10, "end_index": 7},
        {"gb_buffer": "000001000000", "code": 9, "end_index": 6},
        {"gb_buffer": "000010000000", "code": 8, "end_index": 5},
        {"gb_buffer": "000100000000", "code": 7, "end_index": 4},
        {"gb_buffer": "001000000000", "code": 6, "end_index": 3},
        {"gb_buffer": "010000000000", "code": 5, "end_index": 3},
        {"gb_buffer": "011000000000", "code": 4, "end_index": 3},
        {"gb_buffer": "100000000000", "code": 3, "end_index": 3},
        {"gb_buffer": "101000000000", "code": 2, "end_index": 3},
        {"gb_buffer": "110000000000", "code": 1, "end_index": 3},
        {"gb_buffer": "111000000000", "code": 0, "end_index": 3},
    ]
    
    vlc_test(expected_results, vlc.run7_vlc)

