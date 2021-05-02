def install_start_end_marker(name: str, length: float) -> str:
    """
    Method to add end marker.

    Arguments:
    ----------
    name    : str
        name of the sequence to be edited
    length      : float
        length of the lattice

    Returns:
    --------
    Madx input string to install the elements.
    """
    # define  start and end marker
    text = "{:12}: {:12};\n".format("MSTART", "MARKER")
    text += "{:12}: {:12};\n\n".format("MEND", "MARKER")

    # start sequence edit
    text += "USE, SEQUENCE={};\n".format(name)
    text += "SEQEDIT, SEQUENCE = {};  \nFLATTEN;\n".format(name)

    # install start and end marker
    line = "INSTALL, ELEMENT = {:16}, AT = {:12.6f};\n".format("MSTART", 0.00000)
    text += line
    line = "INSTALL, ELEMENT = {:16}, AT = {:12.6f};\n".format("MEND", length)
    text += line

    # end sequence edit
    text += "FLATTEN;\nENDEDIT;"

    return text
