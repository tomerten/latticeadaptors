from collections import defaultdict
from itertools import chain

import matplotlib
import matplotlib.patches as mpatches
import matplotlib.path as mpath
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from cycler import cycler
from matplotlib import pyplot as plot
from matplotlib.collections import PatchCollection
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
from termcolor import colored

from ..parsers.madx_seq_parser import parse_from_madx_sequence_string


def draw_brace(ax, xspan, text, yshift=0.0):
    """Draws an annotated brace on the x axes."""
    xmin, xmax = xspan
    xspan = xmax - xmin
    ax_xmin, ax_xmax = ax.get_xlim()
    xax_span = ax_xmax - ax_xmin
    ymin, ymax = ax.get_ylim()
    yspan = ymax - ymin
    resolution = int(xspan / xax_span * 100) * 2 + 1  # guaranteed uneven
    beta = 300.0 / xax_span  # the higher this is, the smaller the radius

    x = np.linspace(xmin, xmax, resolution)
    x_half = x[: resolution // 2 + 1]
    y_half_brace = 1 / (1.0 + np.exp(-beta * (x_half - x_half[0]))) + 1 / (
        1.0 + np.exp(-beta * (x_half - x_half[-1]))
    )
    y = np.concatenate((y_half_brace, y_half_brace[-2::-1]))
    y = ymin + +yshift + (0.05 * y - 0.01) * yspan  # adjust vertical position

    ax.autoscale(False)
    ax.plot(x, y, color="black", lw=1)

    ax.text((xmax + xmin) / 2.0, ymin + 0.07 * yspan, text, ha="center", va="bottom")


def Beamlinegraph_compare_from_seq_files(seqfile1, seqfile2, start=0.0, stop=None):
    """
    Method to compare location of beam line elements,
    where the positions are extracted from a MADX
    sequence file.

    Arguments:
    ----------
    seqfile1    : str
        input seqfile 1
    seqfile2    : str
        input seqfile 2
    start       :
        s location of start
    stop        :
        s location of stop

    """
    _REQUIRED_COLUMNS = ["pos", "name", "L"]
    _RECTANGLE_ELEMENTS = [
        "SBEND",
        "RBEND",
        "KICKER",
        "VKICKER",
        "HKICKER",
        "QUADRUPOLE",
        "SEXTUPOLE",
        "RFCAVITY",
        "DRIFT",
    ]
    _COLMAP = {
        "SBEND": "#0099FF",
        "RBEND": "#0099FF",
        "KICKER": "#0099FF",
        "VKICKER": "#0099FF",
        "HKICKER": "#0099FF",
        "QUADRUPOLE": "green",
        "SEXTUPOLE": "#FF99FF",
        "RFCAVITY": "#08bad1",
        "MARKER": "red",
        "MONITOR": "black",
        "DIPEDGE": "blue",
        "DRIFT": "#D0D0D0",
    }

    with open(seqfile1, "r") as f:
        seqfilestr1 = f.read()

    with open(seqfile2, "r") as f:
        seqfilestr2 = f.read()

    name1, len1, table1 = parse_from_madx_sequence_string(seqfilestr1)
    name2, len2, table2 = parse_from_madx_sequence_string(seqfilestr2)

    # check if columns are ok
    for c in _REQUIRED_COLUMNS:
        assert c in table1.columns
        assert c in table2.columns

    # find range to plot
    if stop is None:
        stop = max(len1, len2)
        # idxmax_pos = table1["pos"].idxmax()
        # stop = table1.loc[idxmax_pos, "pos"] + table1.loc[idxmax_pos, "L"]
    else:
        table1 = table1.loc[table1["pos"].between(start, stop)]
        table2 = table2.loc[table2["pos"].between(start, stop)]

    _ = plt.figure(figsize=(16, 6))
    axis = plt.gca()

    offset_array = np.array([0.0, -0.5])

    for _, row in table1.iterrows():
        col = _COLMAP[row.family.upper()]

        if row.family in _RECTANGLE_ELEMENTS:
            axis.add_patch(
                mpatches.Rectangle(
                    np.array([row.pos - row.L / 2, 0.0]) + offset_array,
                    row.L,
                    0.33,
                    color=col,
                    alpha=1.0,
                )
            )
            axis.vlines(
                row.pos - row.L / 2,
                offset_array[1],
                0,
                linestyle="dashed",
                color="gray",
                linewidth=1,
            )
            axis.vlines(
                row.pos + row.L / 2,
                offset_array[1],
                0,
                linestyle="dashed",
                color="gray",
                linewidth=1,
            )

        else:
            Path = mpath.Path
            h = 1.0
            offs_mon = np.array([0.0, 0.03])

            verts = np.array(
                [
                    (0, h),
                    (0, -h),
                ]
            )

            codes = [Path.MOVETO, Path.LINETO]

            verts += offs_mon

            path = mpath.Path(verts + offset_array + np.array([row.pos, 0.0]), codes)
            patch = mpatches.PathPatch(path, color=col, lw=1, alpha=1.0 * 0.5)
            axis.add_patch(patch)

        axis.annotate(
            row.family + ": " + row["name"],
            xy=(row.pos, 0),
            # xycoords='data',
            xytext=(row.pos, 0) + offset_array,
            # textcoords='data',
            horizontalalignment="left",
            # arrowprops=dict(arrowstyle="simple",),# connectionstyle="arc3,rad=+0.2"),
            # bbox=dict(boxstyle="round", facecolor="w", edgecolor="0.5", alpha=0.9),
            fontsize=8,
            rotation=90,
        )

    offset_array = np.array([0.0, 0.5])

    for _, row in table2.iterrows():
        col = _COLMAP[row.family.upper()]

        if row.family in _RECTANGLE_ELEMENTS:
            axis.add_patch(
                mpatches.Rectangle(
                    np.array([row.pos - row.L / 2, 0.0]) + offset_array,
                    row.L,
                    0.33,
                    color=col,
                    alpha=1.0,
                )
            )
            axis.vlines(
                row.pos - row.L / 2,
                offset_array[1],
                0,
                linestyle="dashed",
                color="red",
                linewidth=1,
            )
            axis.vlines(
                row.pos + row.L / 2,
                offset_array[1],
                0,
                linestyle="dashed",
                color="red",
                linewidth=1,
            )
        else:
            Path = mpath.Path
            h = 1.0
            offs_mon = np.array([0.0, 0.03])

            verts = np.array(
                [
                    (0, h),
                    (0, -h),
                ]
            )

            codes = [Path.MOVETO, Path.LINETO]

            verts += offs_mon

            path = mpath.Path(verts + offset_array + np.array([row.pos, 0.0]), codes)
            patch = mpatches.PathPatch(path, color=col, lw=1, alpha=1.0 * 0.5)
            axis.add_patch(patch)

        axis.annotate(
            row.family + ": " + row["name"],
            xy=(row.pos, 0),
            # xycoords='data',
            xytext=(row.pos, 0) + offset_array,
            # textcoords='data',
            horizontalalignment="left",
            # arrowprops=dict(arrowstyle="simple",),# connectionstyle="arc3,rad=+0.2"),
            # bbox=dict(boxstyle="round", facecolor="w", edgecolor="0.5", alpha=0.9),
            fontsize=8,
            rotation=90,
        )

    plt.xlim(start, stop)
    plt.ylim(-1.1, 1.1)
    plt.xlabel("S[m]")
    #     plt.grid()
    return plt, axis


def Beamlinegraph_from_seq_file(
    seqfile, start=0.0, stop=None, offset_array=[0.0, 0.0], anno=True, size=(12, 6)
):
    _REQUIRED_COLUMNS = ["pos", "name", "L"]
    _RECTANGLE_ELEMENTS = ["SBEND", "RBEND", "KICKER", "VKICKER", "HKICKER", "DRIFT"]
    _MIN_HEIGTH = 0.1
    _MAX_HEIGTH = 10.0

    with open(seqfile, "r") as f:
        seqfilestr = f.read()

    name, length, table = parse_from_madx_sequence_string(seqfilestr)

    # check if columns are ok
    for c in _REQUIRED_COLUMNS:
        assert c in table.columns

    # find range to plot
    if stop is None:
        # idxmax_pos = table["pos"].idxmax()
        # stop = table.loc[idxmax_pos, "pos"] + table.loc[idxmax_pos, "L"]
        stop = length
    else:
        table = table.loc[table["pos"].between(start, stop)]

    #    print(start, stop)

    element_families = table.family.unique()

    # determine max plot heights
    if any(i in element_families for i in _RECTANGLE_ELEMENTS):
        angle_max = abs(table.ANGLE.max())

    if "QUADRUPOLE" in element_families:
        k_max = abs(table.K1.max())

    _ = plt.figure(figsize=size)
    axis = plt.gca()

    for _, row in table.iterrows():
        if row.family in _RECTANGLE_ELEMENTS:
            axis.add_patch(
                mpatches.Rectangle(
                    np.array([row.pos - row.L / 2, 0.0]) + offset_array,
                    row.L,
                    np.sign(row.ANGLE) * _MIN_HEIGTH + row.ANGLE / angle_max * (1 - _MIN_HEIGTH),
                    color="#0099FF",
                    alpha=1.0,
                )
            )

        elif row.family.upper() == "QUADRUPOLE":
            if row.K1 >= 0:
                # FOCUSSING QUAD
                axis.add_patch(
                    mpatches.Ellipse(
                        offset_array + np.array([row.pos, 0.0]),
                        row.L,
                        _MIN_HEIGTH + abs(row.K1 / k_max) * (1 - _MIN_HEIGTH),
                        color="green",
                        alpha=1.0,
                    )
                )
            else:
                Path = mpath.Path
                h = _MIN_HEIGTH + abs(row.K1 / k_max) * (
                    1 - _MIN_HEIGTH
                )  # abs(row.K1 / k_max) + _MIN_HEIGTH / 2
                dx = row.L
                verts = np.array(
                    [
                        (dx, h),
                        (-dx, h),
                        (-dx / 4, 0),
                        (-dx, -h),
                        (dx, -h),
                        (dx / 4, 0),
                        (dx, h),
                    ]
                )

                codes = [
                    Path.MOVETO,
                    Path.LINETO,
                    Path.CURVE3,
                    Path.LINETO,
                    Path.LINETO,
                    Path.CURVE3,
                    Path.CURVE3,
                ]

                path = mpath.Path(verts + offset_array + np.array([row.pos, 0.0]), codes)
                patch = mpatches.PathPatch(path, color="green", alpha=1.0)
                axis.add_patch(patch)
        elif row.family in ["SEXTUPOLE"]:
            axis.add_patch(
                mpatches.RegularPolygon(
                    np.array([row.pos, 0.0]) + offset_array,
                    6,
                    row.L / 2,
                    color="#FF99FF",
                    alpha=1.0,
                )
            )
        elif row.family in ["MONITOR"]:
            Path = mpath.Path
            h = 0.25
            offs_mon = np.array([0.0, 0.03])

            verts = np.array([(0, h), (0, -h), (h, 0), (-h, 0)])

            codes = [Path.MOVETO, Path.LINETO, Path.MOVETO, Path.LINETO]

            verts += offs_mon

            path = mpath.Path(verts + offset_array + np.array([row.pos, 0.0]), codes)
            patch = mpatches.PathPatch(path, color="black", lw=2, alpha=1.0 * 0.5)
            axis.add_patch(patch)
            axis.add_patch(
                mpatches.Circle(
                    offset_array + offs_mon + np.array([row.pos, 0.0]),
                    h / 2,
                    color="black",
                    alpha=1.0 * 0.25,
                )
            )
        elif row.family in ["MARKER"]:
            Path = mpath.Path
            h = 1.0
            offs_mon = np.array([0.0, 0.03])

            verts = np.array(
                [
                    (0, h),
                    (0, -h),
                ]
            )

            codes = [Path.MOVETO, Path.LINETO]

            verts += offs_mon

            path = mpath.Path(verts + offset_array + np.array([row.pos, 0.0]), codes)
            patch = mpatches.PathPatch(path, color="red", lw=2, alpha=1.0 * 0.5)
            axis.add_patch(patch)

        elif row.family in ["CAVITY"]:
            axis.add_patch(
                mpatches.Ellipse(
                    np.array([row.pos - row.L, 0.0]),
                    row.L,
                    2 * row.L,
                    angle=0,
                    color="#08bad1",
                    alpha=1 * 0.5,
                )
            )

        elif row.family in ["RFMODE"]:
            axis.add_patch(
                mpatches.Ellipse(
                    np.array([row.pos - row.L / 2, 0.0]),
                    row.L,
                    10 * row.L,
                    angle=0,
                    color="#f2973d",
                    alpha=1 * 0.5,
                )
            )

        elif row.family in ["DRIFT"]:
            axis.add_patch(
                mpatches.Rectangle(
                    np.array([row.pos - row.L / 2, -_MIN_HEIGTH]),
                    row.L,
                    2 * _MIN_HEIGTH,
                    color="black",
                    alpha=1 * 0.4,
                )
            )

        if anno:
            annotation = axis.annotate(
                row.family + ": " + row["name"],
                xy=(row.pos + offset_array[0], 0 + offset_array[1]),
                # xycoords='data',
                xytext=(row.pos + offset_array[0], 0 + offset_array[1]),
                # textcoords='data',
                horizontalalignment="left",
                # arrowprops=dict(arrowstyle="simple",),# connectionstyle="arc3,rad=+0.2"),
                # bbox=dict(boxstyle="round", facecolor="w", edgecolor="0.5", alpha=0.9),
                fontsize=8,
                rotation=90,
            )
    plt.xlim(start, stop)
    plt.ylim(-1.1, 1.1)
    plt.xlabel("S[m]")
    #     plt.grid()
    return plt, axis


def twissplot(
    tw, cols=["betx", "bety", "dx"], cpymadtwiss=True, beamlinegraph=False, *args, **kwargs
):
    """
    Method to plot columns from the twiss table output using cpymadtwiss.
    """
    if cpymadtwiss:
        if beamlinegraph:
            plot, ax = Beamlinegraph_from_seq(
                kwargs.get("sequence"),
                offset_array=kwargs.get("offset_array", np.array([0.0, 0.0])),
                start=kwargs.get("start", 0.0),
                stop=kwargs.get("stop", None),
                anno=kwargs.get("anno", False),
            )
        else:
            _ = plt.figure(figsize=kwargs.get("size", (12, 6)))
            plot = plt.gcf()
            ax = plt.gca()

        linestyle_cycler = ["-", "--", ":", "-."]
        if isinstance(tw, list):
            for i, twi in enumerate(tw):
                ax.set_prop_cycle(
                    cycler(
                        "color",
                        [
                            "#1f77b4",
                            "#ff7f0e",
                            "#2ca02c",
                            "#d62728",
                            "#9467bd",
                            "#8c564b",
                            "#e377c2",
                            "#7f7f7f",
                            "#bcbd22",
                            "#17becf",
                        ],
                    )
                    * cycler("linestyle", [linestyle_cycler[i]])
                )
                # ax.rc('axes', prop_cycle=linestyle_cycler)
                for col in cols:
                    ax.plot(twi.get("s"), twi.get(col), label=col + "_{}".format(i))
        else:
            for col in cols:
                ax.plot(tw.get("s"), tw.get(col), label=col)

        ax.legend()
        ax.relim()
        ax.autoscale()
        return plot, ax

    else:
        print("Not implemented yet!!!")
        pass
