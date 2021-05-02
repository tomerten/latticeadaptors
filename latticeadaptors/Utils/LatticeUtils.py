import os

import pandas as pd

from .latticeparser import parse_madx_seq


def compare_seq_center_positions(seqfile1, seqfile2):
    """
    Method to compare locations of elements in two
    MADX sequence files.

    Arguments:
    ----------
    seqfile1    :   str
        path to first seq file
    seqfile2    :   str
        path to second seq file

    Returns:
    --------
    eq  :   pandas dataframe
        frame containing locations and names of elements at identical centre positions
    diff:   pandas dataframe
        frame containing locations and names of elements at different centre positions

    """
    assert os.path.isfile(seqfile1)
    assert os.path.isfile(seqfile2)

    with open(seqfile1, "r") as f:
        seqstr1 = f.read()

    with open(seqfile2, "r") as f:
        seqstr2 = f.read()

    table1 = parse_madx_seq(seqstr1)[["name", "pos"]]
    table2 = parse_madx_seq(seqstr2)[["name", "pos"]]

    eq = pd.merge(table1, table2, on=["pos"], how="inner")
    diff = table1[~table1["pos"].isin(table2["pos"])]

    return eq, diff


def dipole_split_angles_to_dict(
    dipole_name, dipole_len, dipole_bend_angle_rad, angle_list, verbose=True
):
    """
    Method to generate a dictionary that is used by the split_dipoles method
    to split the dipoles over the angle list given in angle_list.
    Verbose allows to print the output for debugging.

    Arguments:
    ----------
    dipole_name             :   str
        name of the dipole - same as name in dataframe used in split_dipoles as input - becomes key
    dipole_len              :   float
        length of the dipole
    dipole_bend_angle_rad   :   float
        bending angle of the dipole in rad
    angle_list              :   list of floats [deg]
        list of splitting angles - from start of dipole -in deg
    verbose                 :   boolean
        flag to print processing output

    IMPORTANT NOTE:
    ---------------
    Auto adds half angle split and final angle for full magnet.

    Returns:
    --------
    Dict containing split angles in rad and split lengths.
    Main key is dipole name, sub keys are "length" and "angles".
    """
    _dict = {dipole_name: dict()}

    dipole_bend_angle_deg = np.rad2deg(dipole_bend_angle_rad)
    dipole_bend_radius = dipole_len / dipole_bend_angle_rad

    if verbose:
        print("Dipole length [m]       : {:12.6f}".format(dipole_len))
        print("Dipole Bend Angle [rad] : {:12.6f}".format(dipole_bend_angle_rad))
        print("Dipole Bend Angle [deg] : {:12.6f}".format(dipole_bend_angle_deg))
        print("Dipole Bend Radius [m]  : {:12.6f}".format(dipole_bend_radius))
        print()
        print()

    split_angles_BM_deg = np.array(
        sorted(angle_list + [dipole_bend_angle_deg / 2, dipole_bend_angle_deg])
    )
    split_angles_BM_cum_rad = np.deg2rad(split_angles_BM_deg)
    split_angles_BM_rad = np.r_[split_angles_BM_cum_rad[0], np.diff(split_angles_BM_cum_rad)]
    split_lengths_cum_BM = split_angles_BM_cum_rad * dipole_bend_radius
    split_lengths_BM = np.r_[split_lengths_cum_BM[0], np.diff(split_lengths_cum_BM)]

    if verbose:
        print(
            "BM splitting angles               [deg] : {}".format(
                "".join(["{:12.6f}".format(a) for a in split_angles_BM_deg])
            )
        )
        print(
            "BM splitting angles  - cumulative [rad] : {}".format(
                "".join(["{:12.6f}".format(a) for a in split_angles_BM_cum_rad])
            )
        )
        print(
            "BM splitting angles  - individual [rad] : {}".format(
                "".join(["{:12.6f}".format(a) for a in split_angles_BM_rad])
            )
        )
        print(
            "BM splitting lengths - cumulative [m]   : {}".format(
                "".join(["{:12.6f}".format(a) for a in split_lengths_cum_BM])
            )
        )
        print(
            "BM splitting lengths - individual [m]   : {}".format(
                "".join(["{:12.6f}".format(a) for a in split_lengths_BM])
            )
        )
        print()

    _dict[dipole_name] = {"lengths": split_lengths_BM, "angles": split_angles_BM_rad}

    return _dict


def split_dipoles(df, _dict, halfbendangle):
    """
    Method to split the dipole given in the
    dataframe according the data given in _dict.

    Arguments:
    ----------
    df              :   pd.DataFrame
        seq table reduced to dipoles to split
    _dict           :   dict
        output of dipole_split_angles_to_dict joined as dict for all
        dipoles in df
    halfbendangle   :   float
        half bending angle for the dipoles
    """
    # init output
    newdf = pd.DataFrame()

    # loop over the dipoles
    for j, row in df.iterrows():
        lengths = _dict[row["name"]]["lengths"]
        angles = _dict[row["name"]]["angles"]

        # calculate the center positions of the splits
        end_pos = lengths.cumsum() + row.pos - row.L / 2
        center_pos = end_pos - (lengths / 2)

        # count splits per magnet
        aports = 1
        bports = 1
        cum_angle = 0

        # loop over the splitting angles for this specific dipole
        for i, (angle, l, pos) in enumerate(zip(angles, lengths, center_pos)):
            # for each angle create a new seq table entry
            newrow = row.copy()
            cum_angle += angle

            # naming depends on magnet number in the sector
            if "BM1" in row["name"]:
                M = 1
            else:
                M = 2

            # add marker
            markerrow = row.copy()
            markerrow.family = "MARKER"
            markerrow.L = 0.000000
            markerrow = markerrow.drop(labels=["E1", "E2", "K1", "K2", "ANGLE"])

            # naming
            # beam ports A in first half of the magnet
            # beam ports B in second half of the magnet
            # number each per split number
            if cum_angle - halfbendangle < -1e-6:
                name = row["name"] + "1_{}_deg".format(
                    ("{:2.2f}".format(np.rad2deg(cum_angle))).replace(".", "p").strip()
                )
                markerrow["name"] = "MBEAMPORT_{}A{}".format(M, aports)
                aports += 1
            elif abs(cum_angle - halfbendangle) < 1e-6:
                name = row["name"] + "1_{}_deg".format(
                    ("{:2.2f}".format(np.rad2deg(cum_angle))).replace(".", "p").strip()
                )
                markerrow["name"] = (
                    "M"
                    + row["name"]
                    + "_MIDDLE".format(
                        ("{:2.2f}".format(np.rad2deg(cum_angle))).replace(".", "p").strip()
                    )
                )
            else:
                name = row["name"] + "2_{}_deg".format(
                    ("{:2.2f}".format(np.rad2deg(cum_angle))).replace(".", "p").strip()
                )
                markerrow["name"] = "MBEAMPORT_{}B{}".format(M, bports)
                bports += 1

            newrow["name"] = name

            # updating angles
            newrow.ANGLE = angle

            # updating lengths
            newrow.L = l

            # updating center position
            newrow.pos = pos
            markerrow.pos = pos + l / 2

            # if at is already in columns update it
            if "at" in newrow.index:
                newrow["at"] = pos

            # update E1 E2
            if i != 0:
                newrow.E1 = 0.000000

                if i != len(angles) - 1:
                    newrow.E2 = 0.000000
            else:
                newrow.E2 = 0.000000

            # add marker only if not at end of magnet
            if abs(cum_angle - 2 * halfbendangle) > 1e-6:
                newdf = newdf.append(markerrow)

            newdf = newdf.append(newrow)

    return newdf.reset_index(drop=True)
