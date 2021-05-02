from json import load
from pathlib import Path

import pandas as pd

from ..Utils.Utils import save_string

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
    save_string(parse_table_to_madx_sequence_string(name, length, df), filename)


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


def parse_table_to_elegant_file(name: str, df: pd.DataFrame, filename: str) -> None:
    save_string(parse_table_to_elegant_string(name, df), filename)


def parse_table_to_tracy_string(latname: str, df: pd.DataFrame) -> str:
    """
    Method to transform the MADX seq table to tracy lattice string.
    """

    # init output
    text = """"""
    template_marker = "{}: Marker;".format
    template_bpm = "{}: Beam Position Monitor;".format
    template_drift = "{}: Drift, {};".format
    template_bend = "{}: Bending, {}, N = Nbend, Method = 4;".format
    template_quad = "{}: Quadrupole, {}, N = Nquad, Method = 4;".format
    template_sext = "{}: Sextupole, {}, N = Nsext, Method = 4;".format
    template_oct = "{}: Multipole, L = {}, HOM = (4,{}/6.0,0.0), N = Nsext, Method = 4;".format
    template_cav = "{}: Cavity, {};".format

    lattice_template = "{}: "
    n_elem = 10
    lattice_elements = list(df["name"].values)
    n = len(lattice_elements)
    if n >= n_elem:
        lattice_template += "\n "
    for k in range(2, n + 2):
        if (k - 1) % (n_elem + 1) == 0:
            lattice_template += "\n "
        lattice_template += lattice_elements[k - 2]
        if k < n + 1:
            lattice_template += ", "
        else:
            lattice_template += ";"
    # element_template = "{}: {}, {}".format

    df = df.drop(columns=["pos", "at"], errors="ignore")
    lattice = lattice_template.format(latname)

    df = df.drop_duplicates()
    # loop over the rows of the frame
    for _, row in df.iterrows():
        # get the element family to check against allowed attrs
        keyword = TO_TRACY_ELEMENTS[row["family"]]
        name = row["name"]

        # get allowed attrs - to distinguish madx from elegant columns
        allowed_attrs = TRACY_ATTRIBUTES[keyword]
        # print(allowed_attrs)

        # line = ""
        # name and element type
        # line += "{:16}: {:12}, ".format(row["name"], keyword)

        # remove non attrs from columns
        row = row.drop(["name", "at", "family", "end_pos", "sector"], errors="ignore").dropna()
        # print(row.index)
        # update the indices

        try:
            row.index = [TO_TRACY_ATTR[c] for c in row.index if TO_TRACY_ATTR[c] != ""]
            # row.index = [TO_TRACY_ATTR[c] for c in row.index if c in allowed_attrs]
            nrow = row.index
        except:
            nrow = [TO_TRACY_ATTR[c] for c in row.index if TO_TRACY_ATTR[c] != ""]
            # nrow = [TO_TRACY_ATTR[c] for c in row.index if c in allowed_attrs]

        if keyword == "bpm":
            line = template_bpm(name)
        elif keyword == "marker":
            line = template_marker(name)
        elif keyword == "drift":
            line = template_drift(name, "L = {}".format(row["L"]))
        elif keyword == "bend":
            new_row = {"L": row["L"]}
            new_row["T"] = np.degrees(row["T"])

            if "Roll" in nrow:
                new_row["Roll"] = np.degrees(row.get("Roll", None))

            if "Gap" in nrow:
                new_row["Gap"] = 4.0 * row.Gap * row.loc_fint

            if "T1" in nrow:
                new_row["T1"] = np.degrees(row.T1)
            if "T2" in nrow:
                new_row["T2"] = np.degrees(row.T2)
            if "K" in nrow:
                new_row["K"] = row.K

            line = template_bend(
                name,
                ", ".join(
                    [
                        "{} = {:17.15f}".format(k, v)
                        if k not in ["L", "K"]
                        else "{} = {:8.6f}".format(k, v)
                        for k, v in new_row.items()
                    ]
                ),
            )
            # line += ", N = Nbend, Method = 4;"

        elif keyword == "quad":
            line = template_quad(
                name,
                ", ".join(
                    ["{} = {:8.6f}".format(k, v) for k, v in row.items() if k in allowed_attrs]
                ),
            )
            # line += ", N = Nquad, Method = 4;"

        elif keyword == "sext":
            line = template_sext(
                name,
                ", ".join(
                    [
                        "{} = {:8.6f}".format(k, v) if k != "K" else "{} = {}/2.0".format(k, v)
                        for k, v in row.items()
                        if k in allowed_attrs
                    ]
                ),
            )
            # line += ", N = Nsext, Method = 4;"
        elif keyword == " oct1":
            line = template_oct(name, row["L"], row["K"])

        elif keyword == "cavity":
            new_row = {"L": row["L"]}
            new_row["Frequency"] = row.get("Frequency", 0.0)
            new_row["Voltage"] = row.get("Voltage", 0.0)
            new_row["phi"] = row.get("phi", 0)

            line = template_cav(
                name,
                ", ".join(
                    [
                        "{} = {:17.15f}".format(k, float(v))
                        if k not in ["L"]
                        else "{} = {:8.6f}".format(k, float(v))
                        for k, v in new_row.items()
                    ]
                ),
            )

        line += "\n"

        # add line to text
        text += line
        # print(text)
    text += "\n\n"
    text += lattice

    text += "\n\n"
    text += "ring: {};\n\n".format(latname)
    text += "cell: ring, symmetry = 1;"
    text += "\n\nend;"

    return text


def parse_table_to_tracy_file(latname: str, df: pd.DataFrame, filename: str) -> None:
    """Method to transform the MADX seq table to tracy lattice and write to file."""
    save_string(parse_table_to_tracy_string(latname, df), filename)
