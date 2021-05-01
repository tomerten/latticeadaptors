import pandas as pd
import pytest
from latticeadaptors import __version__, parse_from_madx_sequence_string
from pandas.testing import assert_frame_equal

# test inputs and outputs
seq_str_test = [
    (
        """
    testmarker : MARKER;
    """,
        None,
        0.0,
        pd.DataFrame([{"family": "MARKER", "name": "TESTMARKER"}]),
    ),
    (
        """
    FODO: SEQUENCE, L=8;
    QF  , at = 2.000;
    ENDSEQUENCE;
    """,
        "FODO",
        8.0,
        pd.DataFrame([{"name": "QF", "pos": 2.0}]),
    ),
]


def test_version():
    assert __version__ == "0.1.0"


@pytest.mark.parametrize("string, expected_name, expected_len, expected_df", seq_str_test)
def test_parse_from_madx_seqeunce_string(string, expected_name, expected_len, expected_df):
    name, length, df = parse_from_madx_sequence_string(string)

    print(df)
    assert name == expected_name
    assert length == expected_len
    assert_frame_equal(df, expected_df, check_like=True)
