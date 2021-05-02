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


def highlight_cells(data, _list=[], color="yellow"):
    attr = "background-color: {}".format(color)
    if data.ndim == 1:
        is_sel = data.isin(_list)
        return [attr if v else "" for v in is_sel]
    else:
        is_sel = data.isin(_list)
        return pd.DataFrame(np.where(is_sel, attr, ""), index=data.index, columns=data.columns)


def highlight_row(data, _list, column, color="yellow"):
    attr = "background-color: {}".format(color)
    is_sel = pd.Series(data=False, index=data.index)
    is_sel[column] = data.loc[column].isin(_list)
    return [attr if is_sel.any() else "" for v in is_sel]


def display_more(df, maxrows=300, maxcols=100):
    """
    Show more rows and columns of a dataframe.
    """
    with pd.option_context("display.max_rows", maxrows, "display.max_columns", maxcols):
        display(df)
