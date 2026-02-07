import sys
sys.path.append('..')

from lpc_test import lpc_test
from lpc_test_expected import lpc_test_expected
from lpc_test_context import lpc_test_context



def test_lpc_base():
    template_test("base")

def test_lpc_scale_and_rounding():
    template_test("scale_and_rounding")


def template_test(key):
    expected_list = lpc_test_expected[key]
    context_list = lpc_test_context[key]
    
    for expected_samples, callback_context_tweaker in zip(expected_list, context_list):
        lpc_test(expected_samples, callback_context_tweaker)
