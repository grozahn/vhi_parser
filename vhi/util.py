import os
import sqlite3
import multiprocessing as mp

from time import strftime
from typing import List, Iterable, Any

from vhi.parser import Parser, WeekRecord


def mktree(path: str) -> int:
    r"""
    Create simple hierarchy of directories.

    Works exacly like "mkdir -p" shell command

    :returns OSError.errno or 0 in case of success
    """

    current = ""
    for d in path.split(os.path.sep):
        current = os.path.join(current, d)
        if not os.path.exists(current):
            try:
                os.mkdir(current)
            except OSError as e:
                return -e.errno
    return 0


def chunkify(lst: List[Any], n_chunks: int, step: int) -> List[Any]:
    r"""
    Split list into chunks
    With every iteration returns equal chunk of list
    Used for equally splitting data between threads/processes

    :param lst: source list
    :param n_chunks: count of chunks to split on
    :param step: indicises current iteration
    :returns: chunk of source list
    :rtype: List[Any]
    """

    lst_len = len(lst)
    chunksz = lst_len // n_chunks

    tail = lst_len % n_chunks if step == n_chunks else 0

    start = (step - 1) * chunksz
    return lst[start:start + chunksz + tail]


def gen_columns_labels() -> List[str]:
    r"""
    Generate csv table columnn names
    Names are percentages in range from 0 to 100 with 5% step
    Example: ['0-5%', '5-10%', '10-15%', ... '95%-100%']

    returns: list with names
    rtype: List[str]
    """
    return ["{}-{}%".format(i, i + 5) for i in range(0, 100, 5)]


def gtk_rgb_to_hex(rgb: str) -> str:
    r"""
    Converts Gdk.RGBA color to regular #rrggbb format

    :param rgb: string in format of "Gtk.RGB(%d, %d, %d)"
    :returns: string in format "#%x%x%x"
    :rtype: str
    """

    return "#{:02x}{:02x}{:02x}".format(*[
        int(num) for num in rgb[rgb.find('(') + 1:-1].split(",")[:3]])
