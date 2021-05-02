from json import load
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent

# MADX
with (BASE_DIR / "../mapfiles/madx_columns.json").open() as file:
    MADX_ATTRIBUTES = load(file)

# ELEGANT
with (BASE_DIR / "../mapfiles/elegant_columns.json").open() as file:
    ELEGANT_ATTRIBUTES = load(file)

with (BASE_DIR / "../mapfiles/elegant_element_map.json").open() as file:
    TO_ELEGANT_ELEMENTS = load(file)

with (BASE_DIR / "../mapfiles/elegant_attribute_map.json").open() as file:
    TO_ELEGANT_ATTR = load(file)

# TRACY
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


def _parse_table_to_madx_sequence_part(name: str, length: float, df: pd.DataFrame) -> str:
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


def parse_table_to_madx_sequence_string(name: str, length: float, df: pd.DataFrame) -> str:
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
    text += _parse_table_to_madx_sequence_part(name, length, df)

    return text


def parse_table_to_madx_sequence_file(
    name: str, length: float, df: pd.DataFrame, filename: str
) -> None:
    """Method to parse table to madx sequence and save in file."""
    with open(filename, "w") as f:
        f.write(parse_table_to_madx_sequence_string(name, length, df))


def parse_table_to_madx_install_str(name: str, df: pd.DataFrame) -> str:
    """
    Method to parse table to MADX SEQEDIT INSTALL string.
    This can be saved to file to load via CALL or used
    directly as MADX input string using MADX().input(str) from
    cpymad package.

    Arguments:
    ----------
    name    : str
        name of the sequence to be edited
    df      : pd.DataFrame
        table with elements to install (requires name, at as columns)

    Returns:
    --------
    Madx input string to install the elements.

    """

    # start sequence edit
    text = "USE, SEQUENCE={};\n".format(name)
    text += "SEQEDIT, SEQUENCE = {};  \nFLATTEN;\n".format(name)
    for _, row in df.iterrows():
        line = "INSTALL, ELEMENT = {:16}, AT = {:12.6f};\n".format(row["name"], row["at"])
        text += line

    # end sequence edit
    text += "FLATTEN;\nENDEDIT;"

    return text


def parse_table_to_madx_remove_str(name: str, df: pd.DataFrame) -> str:
    """
    Method to parse a seq table to MADX SEQEDIT REMOVE string.
    This can be saved to file to load via CALL or used directly
    as MADX input string using MADX().input(str) from the cpymad
    package.

    Arguments:
    ----------
    name    : str
        name of the sequence to be edited
    df      : pd.DataFrame
        table with elements to remove (requires name, at as columns)

    Returns:
    --------
    Madx input string to install the elements.
    """
    # start sequence edit
    text = "USE, SEQUENCE={};\n".format(name)
    text += "SEQEDIT, SEQUENCE = {};  \nFLATTEN;\n".format(name)
    for _, row in df.iterrows():
        line = "REMOVE, ELEMENT = {:16};\n".format(row["name"])
        text += line

    # end sequence edit
    text += "FLATTEN;\nENDEDIT;"

    return text


def parse_table_to_elegant_string(name: str, df: pd.DataFrame) -> str:
    """
    Method to transform the MADX seq table to an Elegant lte file
    """

    # init output
    text = """"""
    lattice_template = "{}: LINE=({})".format
    # element_template = "{}: {}, {}".format

    df = df.drop(columns=["pos", "at"], errors="ignore")
    lattice_elements = ", ".join(list(df["name"].values))
    lattice = lattice_template(name, lattice_elements)

    df = df.drop_duplicates()

    # loop over the rows of the frame
    for _, row in df.iterrows():
        # get the element family to check against allowed attrs
        keyword = TO_ELEGANT_ELEMENTS[row["family"]]

        # get allowed attrs - to distinguish madx from elegant columns
        # print(keyword)
        # print(TO_ELEGANT_ATTR)
        allowed_attrs = ELEGANT_ATTRIBUTES[keyword]
        # print(allowed_attrs)

        line = ""

        # name and element type
        line += "{:16}: {:12}, ".format(row["name"], keyword)

        # remove non attrs from columns
        row = row.drop(["name", "at", "family", "end_pos", "sector"], errors="ignore").dropna()
        # nrow = [TO_ELEGANT_ATTR[c] for c in row.index if (TO_ELEGANT_ATTR[c] != "")]
        nrow = [TO_ELEGANT_ATTR[c] for c in row.index if c in allowed_attrs]
        # print(row.index)

        # add allowed madx attributes
        if len(allowed_attrs) > 0 and len(nrow) > 0:
            attr_line = (
                ", ".join(
                    [
                        "{}={:16.12f}".format(c, row[c])
                        if TO_ELEGANT_ATTR[c] in allowed_attrs and not isinstance(row[c], str)
                        else "{}={:16}".format(c, row[c])
                        if TO_ELEGANT_ATTR[c] in allowed_attrs
                        else ""
                        for c in nrow
                        # if TO_ELEGANT_ATTR[c] in allowed_attrs
                    ]
                )
                + "\n"
            )
        else:
            attr_line = "\n"
            line = line[:-2]

        line += attr_line

        # add line to text
        text += line
        # print(text)

    text += "\n\n"
    text += lattice

    return text