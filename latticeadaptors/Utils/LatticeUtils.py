import os

import pandas as pd

from .latticeparser import parse_madx_seq


def compare_seq_center_positions(seqfile1, seqfile2):
    """
    Method to compare locations of elements in two
    MADX sequence files.

    Arguments:
    ----------
    seqfile1    :   str
        path to first seq file
    seqfile2    :   str
        path to second seq file

    Returns:
    --------
    eq  :   pandas dataframe
        frame containing locations and names of elements at identical centre positions
    diff:   pandas dataframe
        frame containing locations and names of elements at different centre positions

    """
    assert os.path.isfile(seqfile1)
    assert os.path.isfile(seqfile2)

    with open(seqfile1, "r") as f:
        seqstr1 = f.read()

    with open(seqfile2, "r") as f:
        seqstr2 = f.read()

    table1 = parse_madx_seq(seqstr1)[["name", "pos"]]
    table2 = parse_madx_seq(seqstr2)[["name", "pos"]]

    eq = pd.merge(table1, table2, on=["pos"], how="inner")
    diff = table1[~table1["pos"].isin(table2["pos"])]

    return eq, diff
