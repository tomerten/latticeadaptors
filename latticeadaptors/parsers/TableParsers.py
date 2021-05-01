from json import load
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent

with (BASE_DIR / "../mapfiles/madx_columns.json").open() as file:
    MADX_ATTRIBUTES = load(file)


def _parse_table_to_madx_definitions(df: pd.DataFrame) -> str:
    """
    Method to parse table to MADX sequence file definitions.

    Arguments:
    ----------
    df  : pd.DataFrame
        Table containing the elements and their attributes.

    """
    # init output
    text = """"""

    df = df.drop(columns=["pos", "at"], errors="ignore")
    df = df.drop_duplicates()
    # loop over the rows of the frame
    for _, row in df.iterrows():
        # get the element family to check against allowed attrs
        keyword = row["family"]

        # get allowed attrs - to distinguish madx from elegant columns
        allowed_attrs = MADX_ATTRIBUTES[keyword].keys()

        # init line
        line = ""

        # name and element type
        line += "{:16}: {:12}, ".format(row["name"], keyword)

        # remove non attrs from columns
        row = row.drop(["name", "at", "family", "end_pos", "sector"], errors="ignore").dropna()

        # add allowed madx attributes
        if len(allowed_attrs) > 0:
            attr_line = (
                ", ".join(
                    [
                        "{}:={}".format(c, row[c])
                        if c in allowed_attrs and c != "NO_CAVITY_TOTALPATH"
                        else "{}={}".format(c, str(row[c]).lower())
                        for c in row.index
                    ]
                )
                + ";\n"
            )
        else:
            attr_line = ";\n"
            line = line[:-2]

        line += attr_line

        # add line to text
        text += line

    return text


def _parse_table_to_madx_sequence_part(name: str, df: pd.DataFrame, length: float) -> str:
    """
    Method to parse a table to the MADX sequence part.

    Arguments:
    ----------
    name    : str
        name of the sequence
    df      : pd.DataFrame
        table containing the elements and their attributes
    length  : float
        length of the sequence (drifts are determined automatically)

    """
    # start the sequence definition
    text = "{}: SEQUENCE, L={};\n".format(name, length)

    # loop over the table rows
    for _, row in df.iterrows():
        line = "{:11}, at = {:12.6f};\n".format(row["name"], row["at"])
        text += line

    # close the sequence definition
    text += "ENDSEQUENCE;"

    return text


def parse_table_to_madx_sequence_string(name: str, df: pd.DataFrame, length: float) -> str:
    """
    Method to parse table to MADX sequence.

    Arguments:
    ----------
    name    : str
        name of the sequence
    df      : pd.DataFrame
        table containing the element data
    length  : float
        length of the sequence

    """
    # parse the element definitions
    text = _parse_table_to_madx_definitions(df)

    # parse the element positions
    text += _parse_table_to_madx_sequence_part(name, df, length)

    return text
