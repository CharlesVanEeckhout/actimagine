import pytest
import sys
sys.path.append('..')

from lpc_test import lpc_test
from lpc_test_expected import lpc_test_expected
from lpc_test_context import lpc_test_context


@pytest.mark.parametrize(
    "key", lpc_test_context.keys()
)
def test_lpc(key):
    expected_list = lpc_test_expected[key]
    context_list = lpc_test_context[key]

    for expected_samples, callback_context_tweaker in zip(expected_list, context_list):
        lpc_test(expected_samples, callback_context_tweaker)
