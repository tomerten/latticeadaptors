import queue

from latticeadaptors import (
    __version__,
    parse_from_madx_sequence_file,
    parse_from_madx_sequence_string,
)


class LatticeAdaptor:
    """Class to convert lattices."""

    def __init__(self, **kwargs):
        self.version = __version__
        self.name = kwargs.get("name", None)
        self.len = kwargs.get("len", 0.0)
        self.table = keargs.get("table", None)

        # roll back
        self.history = queue.LifoQueue()

    def load_from_madx_sequence_string(string: str) -> None:
        """Load lattice from sequence as string"""
        # roll back
        self.history.put((self.name, self.len, self.table))

        self.name, self.len, self.table = parse_from_madx_sequence_string(string)

    def load_from_madx_sequence_file(filename: str) -> None:
        """Load lattice from sequence in file"""
        # roll back
        self.history.put((self.name, self.len, self.table))

        self.name, self.len, self.table = parse_from_madx_sequence_file(filename)
