#!/usr/bin/env python2
import pytest
import numpy as np
from cplpy import run_test, prepare_config, get_test_dir
import os
import re

# -----Velocities TESTS-----

# EXPLANATION:

MD_FNAME = "lammps_vels.in"
MD_ARGS = "-in " + MD_FNAME
MD_EXEC = "lmp_cpl"
CFD_FNAME = "dummyCFD_vels.py"
CFD_ARGS = CFD_FNAME
CFD_EXEC = "python2"
TEST_TEMPLATE_DIR = os.path.join(get_test_dir(), "templates")
TEST_DIR = os.path.dirname(os.path.realpath(__file__))


@pytest.fixture()
def prepare_config_fix(tmpdir):
    prepare_config(tmpdir, TEST_DIR, MD_FNAME, CFD_FNAME)

def name_with_step(fname, step):
    split_fname = re.split('(\W)', fname)
    dot_pos = split_fname.index(".")
    split_fname.insert(dot_pos , str(step))
    return "".join(split_fname)


def compare_vels(tol, lammps_fname="lammps_vels.dat",
                 cfd_fname="cfd_vels.dat", steps=1):

    for s in xrange(steps):
        # Line format of CFD script file -- > x y z vx vy vz
        with open(name_with_step(cfd_fname, s), "r") as cfd_file:
            cfd_lines = cfd_file.readlines()
        cfd_lines = [l[:-1].split(" ") for l in cfd_lines]
        cfd_cells = {}
        for l in cfd_lines:
            cfd_cells[(float(l[0]), float(l[1]), float(l[2]))] = np.array([float(l[3]),
                                                                           float(l[4]),
                                                                           float(l[5])])

        # Line format of LAMMPS file -- > chunk x y z ncount vx vy vz
        with open(lammps_fname, "r") as lammps_file:
            lammps_lines = lammps_file.readlines()
        header = 3
        step_header = 1
        per_step = int(lammps_lines[3].split(" ")[1])
        #NOTE: Jump the first time-step. Initial state.
        begin = header + (step_header + per_step) * (s+1) + 1
        end = begin + per_step
        lammps_lines = lammps_lines[begin:end]
        lammps_lines = [l[:-1].split(" ") for l in lammps_lines]
        lammps_cells = {}
        for l in lammps_lines:
            l = filter(None, l)
            lammps_cells[(float(l[1]), float(l[2]), float(l[3]))] = np.array([float(l[5]),
                                                                              float(l[6]),
                                                                              float(l[7])])

        # Compare each cell velocity up to a certain tolerance
        for cell in cfd_cells.keys():
            try:
                diff_vel = abs(cfd_cells[cell] - lammps_cells[cell])
                if (np.any(diff_vel > tol)):
                    print "Step: %s" % s
                    print "Cell %s value differs in md : %s and cfd: %s" % (str(cell), str(lammps_cells[cell]), str(cfd_cells[cell]))
                    assert False
            except KeyError:
                print "Step: %s" % s
                print "Cell not found: " + str(cell)
                assert False

# -----VELOCITY TESTS-----

# EXPLANATION: See README-test located in this folder.


@pytest.mark.parametrize("cfdprocs, mdprocs, err_msg", [
                         ((3, 3, 3), (3, 3, 3),  ""),
                         ((1, 1, 1), (3, 3, 3),  "")])
def test_velocitiesP2C(prepare_config_fix, cfdprocs, mdprocs, err_msg):
    MD_PARAMS = {"lx": 300.0, "ly": 300.0, "lz": 300.0}
    MD_PARAMS["npx"], MD_PARAMS["npy"], MD_PARAMS["npz"] = mdprocs

    CFD_PARAMS = {"lx": 300.0, "ly": 300.0, "lz": 300.0,
                  "ncx": 15, "ncy": 15, "ncz": 15, }
    CFD_PARAMS["npx"], CFD_PARAMS["npy"], CFD_PARAMS["npz"] = cfdprocs

    CONFIG_PARAMS = {"cfd_bcx": 1, "cfd_bcy": 1, "cfd_bcz": 1,
                     "olap_xlo": 1, "olap_xhi": 15,
                     "olap_ylo": 1, "olap_yhi": 5,
                     "olap_zlo": 1, "olap_zhi": 15,
                     "cnst_xlo": 1, "cnst_xhi": 15,
                     "cnst_ylo": 5, "cnst_yhi": 5,
                     "cnst_zlo": 1, "cnst_zhi": 15,
                     "tstep_ratio": 5, }

    correct = run_test(TEST_TEMPLATE_DIR, CONFIG_PARAMS, MD_EXEC, MD_FNAME, MD_ARGS,
                       CFD_EXEC, CFD_FNAME, CFD_ARGS, MD_PARAMS, CFD_PARAMS, err_msg, True)
    if correct:
        compare_vels(1e-6)
