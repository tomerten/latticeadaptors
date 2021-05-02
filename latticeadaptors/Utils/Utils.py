def is_number(s):
    """Method to check if a value is a number or not."""
    try:
        float(s)
        return True
    except ValueError:
        return False


def filter_family(df, fam):
    """Filter dataframe by family name."""
    _filter = df.family == fam
    return df.loc[_filter].copy().reset_index(drop=True)


def rotate(l, n):
    """
    Method to rotate a list.
    """
    return l[-n:] + l[:-n]


def delete_first_line(file):
    """
    Method to delete first line in a file.
    Used to delete first line of SAVE SEQUENCE output of madx.
    """
    with open(file, "r") as fin:
        data = fin.read().splitlines(True)
    with open(file, "w") as fout:
        fout.writelines(data[1:])


def save_string(string, file):
    """Quick method to save string to file"""
    with open(file, "w") as f:
        f.write(string)
