import os
import pytest
from fsqa import reports
from pkg_resources import resource_filename as pkgrf


@pytest.mark.order(3)
def test_gen_html(tempdir):
    assert os.path.exists(
        reports.gen_html(
            tempdir,
            imgs=[
                str(tempdir / "aseg.svg"),
                str(tempdir / "tlrc.svg"),
                str(tempdir / "lh_infl.svg"),
            ],
            out_file=tempdir / "tmp.html",
            template=pkgrf("fsqa.data", "individual.html"),
        )
    )


@pytest.mark.order(4)
def test_cleanup(tempdir):
    file_exts = [".svg", ".png", ".xfm", ".nii.gz"]
    reports.cleanup(tempdir)
    for ext in file_exts:
        assert not len(list(tempdir.glob(f"*{ext}"))) > 0
