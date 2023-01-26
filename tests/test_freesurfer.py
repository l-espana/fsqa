import pytest
import os
import matplotlib
from fsqa import freesurfer
from pathlib import Path


@pytest.fixture
def subject_dir():
    return Path(f"{os.getenv('FREESURFER_HOME')}/subjects/cvs_avg35")


@pytest.fixture
def incomplete_subject_dir():
    return Path(f"{os.getenv('FREESURFER_HOME')}/subjects/bert")


@pytest.fixture
def failed_recon_all(tempdir):
    with open(tempdir / "scripts" / "recon-all.log", "w") as recon:
        recon.write("recon-all: exited with ERRORS")

    return tempdir


def test_get_colormap():
    cmap = freesurfer.get_colormap(os.getenv("FREESURFER_HOME"))
    assert isinstance(cmap, matplotlib.colors.ListedColormap)


def test_check_reconall(subject_dir):
    assert freesurfer.check_reconall(subject_dir)


def test_check_reconall_incomplete(incomplete_subject_dir):
    with pytest.raises(Exception):
        freesurfer.check_reconall(incomplete_subject_dir)


def test_check_reconall_fail(failed_recon_all):
    assert not freesurfer.check_reconall(failed_recon_all)


@pytest.mark.order(1)
def test_get_tlrc_report(subject_dir, tempdir):
    svg = freesurfer.get_tlrc_report(subject_dir, tempdir)
    assert svg.endswith("svg")


@pytest.mark.order(2)
def test_get_aseg_plots(subject_dir, tempdir):
    imgs = freesurfer.get_aseg_plots(
        os.getenv("FREESURFER_HOME"), subject_dir, tempdir, num_imgs=10
    )
    assert type(imgs) == list
    assert len(imgs) > 0
