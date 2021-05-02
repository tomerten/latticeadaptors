import queue

from latticeadaptors import (
    __version__,
    parse_from_madx_sequence_file,
    parse_from_madx_sequence_string,
    parse_table_to_elegant_file,
    parse_table_to_elegant_string,
    parse_table_to_madx_install_str,
    parse_table_to_madx_remove_str,
    parse_table_to_madx_sequence_file,
    parse_table_to_madx_sequence_string,
    parse_table_to_tracy_file,
    parse_table_to_tracy_string,
)

from .Utils.MadxUtils import install_start_end_marke


class LatticeAdaptor:
    """Class to convert lattices."""

    def __init__(self, **kwargs):
        self.version = __version__
        self.name = kwargs.get("name", None)
        self.len = kwargs.get("len", 0.0)
        self.table = keargs.get("table", None)

        # roll back
        self.history = queue.LifoQueue()

    def load_from_madx_sequence_string(self, string: str) -> None:
        """Load lattice from sequence as string"""
        # roll back
        self.history.put((self.name, self.len, self.table))

        self.name, self.len, self.table = parse_from_madx_sequence_string(string)

    def load_from_madx_sequence_file(self, filename: str) -> None:
        """Load lattice from sequence in file"""
        # roll back
        self.history.put((self.name, self.len, self.table))

        self.name, self.len, self.table = parse_from_madx_sequence_file(filename)

    def parse_table_to_madx_sequence_string(self):
        """Parse table to madx sequence and return it as a string"""
        return parse_table_to_madx_sequence_string(self.name, self.len, self.table)

    def parse_table_to_madx_sequence_file(self, filename):
        """Parse table to madx sequence and write to file"""
        parse_table_to_madx_sequence_file(self.name, self.len, self.table, filename)

    def parse_table_to_elegant_string(self):
        """Parse table to elegant lattice file and return as string."""
        return parse_table_to_elegant_string(self.name, self.table)

    def parse_table_to_elegant_file(self, filename):
        """Parse table to elegant lattice and write to file"""
        parse_table_to_elegant_file(self.name, self.table, filename)

    def parse_table_to_tracy_string(self):
        """Parse table to tracy lattice file and return as string."""
        return parse_table_to_tracy_string(self.name, self.table)

    def parse_table_to_tracy_file(self, filename):
        """Parse table to tracy lattice and write to file"""
        parse_table_to_tracy_file(self.name, self.table, filename)

    def madx_sequence_add_start_end_marker_string(self):
        """Return madx string to install marker at start and at end of lattice"""
        return install_start_end_marker(self.name, self.len)

    def add_drifts(self):
        """Method to add back drifts to sequence."""
        self.history.put((self.name, self.len, self.table))

        df = self.table.copy()
        df.reset_index(inplace=True, drop=True)
        name = "D"
        family = "DRIFT"

        df.loc[df.L.isna(), "L"] = 0
        newrows = []
        ndrift = 0
        for i, row in df.iterrows():
            # add the row
            newrows.append(pd.DataFrame(row).T)

            # check if next row
            if i < len(df) - 1:
                # check if next row pos is not equal to the current
                nextrow = df.loc[i + 1]
                if nextrow["pos"] > row.pos:
                    ndrift += 1
                    newrow = {}
                    newrow["name"] = name + str(ndrift)
                    newrow["family"] = family
                    newrow["L"] = np.round(
                        (nextrow["pos"] - nextrow["L"] / 2.0) - (row["pos"] + row["L"] / 2.0), 6
                    )
                    newrow["pos"] = (row["pos"] + row["L"] / 2.0) + (newrow["L"] / 2.0)
                    newrows.append(pd.Series(newrow).to_frame().T)
        if nextrow["pos"] < self.len:
            newrow = {}
            newrow["name"] = name + str(ndrift)
            newrow["family"] = family
            newrow["L"] = np.round(self.len - nextrow["pos"], 6)
            newrow["pos"] = (row["pos"] + row["L"] / 2.0) + (newrow["L"] / 2.0)
            newrows.append(pd.Series(newrow).to_frame().T)
        return (pd.concat(newrows)).reset_index(drop=True)
