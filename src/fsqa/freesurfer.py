# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
#
# Copyright 2022 Lezlie España <www.github.com/l-espana>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
FreeSurfer-related operations and utilities.
"""

import os
import glob
import pandas as pd
import numpy as np
from matplotlib import colors
from matplotlib import pyplot as plt
from pkg_resources import resource_filename as pkgrf

from nilearn import plotting
from nipype.interfaces.freesurfer.preprocess import MRIConvert
from nipype.interfaces.fsl import FLIRT
from niworkflows.interfaces.reportlets.registration import SimpleBeforeAfterRPT


def check_reconall(subject_fsdir):
    """
    Verifies that the subject's FreeSurfer recon completed successfully.

    Parameters
    ----------
    subject_fsdir : path or str representing a path to a directory
        Path to a subject's FreeSurfer directory.

    Returns
    -------
    bool
        True if FreeSurfer finished successfully, False otherwise.
    """
    log = os.path.join(subject_fsdir, "scripts", "recon-all.log")
    if os.path.exists(log):
        with open(log, "r") as reconall:
            line = reconall.readlines()[-1]
            if "finished without error" in line:
                return True
            else:
                return False
    else:
        raise Exception("Subject has no recon-all output.")


def get_colormap(freesurfer_home):
    """
    Generates matplotlib colormap from FreeSurfer LUT.
    Code from:
    https://github.com/Deep-MI/qatools-python/blob/freesurfer-module-releases/qatoolspython/createScreenshots.py

    Parameters
    ----------
    freesurfer_home : path or str representing a path to a directory
       Path corresponding to FREESURFER_HOME env var.

    Returns
    -------
    colormap : matplotlib.colors.ListedColormap
        A matplotlib compatible FreeSurfer colormap.
    """
    lut = pd.read_csv(
        os.path.join(freesurfer_home, "FreeSurferColorLUT.txt"),
        sep=" ",
        comment="#",
        header=None,
        skipinitialspace=True,
        skip_blank_lines=True,
    )
    lut = np.array(lut)
    lut_tab = np.array(lut[:, (2, 3, 4, 5)] / 255, dtype="float32")
    lut_tab[:, 3] = 1
    colormap = colors.ListedColormap(lut_tab)

    return colormap


def get_tlrc_report(subject_fsdir, output_dir):
    """
    Computes inverse talairach transform from FreeSurfer output and
    replicates the tkregister2 registration images for QA.

    Parameters
    ----------
    subject_fsdir : path or str representing a path to a directory
        Path to a subject's FreeSurfer directory.
    output_dir : path or str representing a path to a directory
        Working/output directory.

    Returns
    -------
    svg
        SVG file generated from the niworkflows SimpleBeforeAfterRPT
    """
    # get inverse transform
    xfm = np.genfromtxt(
        os.path.join(subject_fsdir, "mri", "transforms", "talairach.xfm.lta"),
        skip_header=5,
        max_rows=4,
    )
    inverse_xfm = np.linalg.inv(xfm)
    np.savetxt(
        os.path.join(output_dir, "inv.xfm"),
        inverse_xfm,
        fmt="%0.8f",
        delimiter=" ",
        newline="\n",
        encoding="utf-8",
    )

    # convert subject original T1 to nifti (for FSL)
    convert = MRIConvert(
        in_file=os.path.join(subject_fsdir, "mri", "orig.mgz"),
        out_file=os.path.join(output_dir, "orig.nii.gz"),
        out_type="niigz",
    )
    convert.run()

    # use FSL to convert template file to subject original space
    flirt = FLIRT(
        in_file=pkgrf("fsqa.data", "mni305.cor.nii.gz"),
        reference=os.path.join(output_dir, "orig.nii.gz"),
        out_file=os.path.join(output_dir, "mni2orig.nii.gz"),
        in_matrix_file=os.path.join(output_dir, "inv.xfm"),
        apply_xfm=True,
        out_matrix_file=os.path.join(output_dir, "out.mat"),
    )
    flirt.run()

    # use white matter segmentation to compare registrations
    report = SimpleBeforeAfterRPT(
        before=os.path.join(subject_fsdir, "mri", "orig.mgz"),
        after=os.path.join(output_dir, "mni2orig.nii.gz"),
        wm_seg=subject_fsdir / "mri" / "wm.mgz",
        before_label="Subject Orig",
        after_label="Template",
        out_report=os.path.join(output_dir, "tlrc.svg"),
    )
    result = report.run()
    output = result.outputs.out_report

    return output


def get_aseg_plots(freesurfer_home, subject_fsdir, output_dir, num_imgs):
    """Generates multiple images. One contains the
    parcellation and segmentation images from FreeSurfer.
    The other contains multiple views of the subject surface in 3d,
    with parcellation information overalyed.

    Parameters
    ----------
    subject_fsdir : path or str representing a path to a directory
        Path to a subject's FreeSurfer directory.
    output_dir : path or str representing a path to a directory
        Working/output directory.
    num_imgs : int, optional
        Number of images to use in the parcellation and
        segmentation image.

    Returns
    -------
    imgs : list
        A list of PNG images generated.
    """
    colormap = get_colormap(freesurfer_home)

    # get parcellation and segmentation images
    plotting.plot_roi(
        os.path.join(subject_fsdir, "mri", "aparc+aseg.mgz"),
        os.path.join(subject_fsdir, "mri", "T1.mgz"),
        cmap=colormap,
        display_mode="mosaic",
        dim=-1,
        cut_coords=num_imgs,
        alpha=0.5,
        output_file=os.path.join(output_dir, "aseg.svg"),
    )
    display = plotting.plot_anat(
        os.path.join(subject_fsdir, "mri", "brainmask.mgz"),
        display_mode="mosaic",
        cut_coords=num_imgs,
        dim=-1,
    )
    display.add_contours(
        os.path.join(subject_fsdir, "mri", "lh.ribbon.mgz"),
        colors="b",
        linewidths=0.5,
        levels=[0.5],
    )
    display.add_contours(
        os.path.join(subject_fsdir, "mri", "rh.ribbon.mgz"),
        colors="r",
        linewidths=0.5,
        levels=[0.5],
    )
    display.savefig(os.path.join(output_dir, "aparc.svg"))
    display.close()

    # get surface images
    hemis = {"lh": "left", "rh": "right"}
    for key, val in hemis.items():
        pial = os.path.join(subject_fsdir, "surf", f"{key}.pial")
        annot = os.path.join(subject_fsdir, "label", f"{key}.aparc.annot")
        inflated = os.path.join(subject_fsdir, "surf", f"{key}.inflated")
        sulc = os.path.join(subject_fsdir, "surf", f"{key}.sulc")
        white = os.path.join(subject_fsdir, "surf", f"{key}.white")

        label_files = {pial: "pial", inflated: "infl", white: "white"}

        for surf, label in label_files.items():
            fig, axs = plt.subplots(2, 3, subplot_kw={"projection": "3d"})
            plotting.plot_surf_roi(
                surf,
                annot,
                hemi=val,
                view="lateral",
                bg_map=sulc,
                bg_on_data=True,
                darkness=1,
                cmap=colormap,
                axes=axs[0, 0],
                figure=fig,
            )
            plotting.plot_surf_roi(
                surf,
                annot,
                hemi=val,
                view="medial",
                bg_map=sulc,
                bg_on_data=True,
                darkness=1,
                cmap=colormap,
                axes=axs[0, 1],
                figure=fig,
            )
            plotting.plot_surf_roi(
                surf,
                annot,
                hemi=val,
                view="dorsal",
                bg_map=sulc,
                bg_on_data=True,
                darkness=1,
                cmap=colormap,
                axes=axs[0, 2],
                figure=fig,
            )
            plotting.plot_surf_roi(
                surf,
                annot,
                hemi=val,
                view="ventral",
                bg_map=sulc,
                bg_on_data=True,
                darkness=1,
                cmap=colormap,
                axes=axs[1, 0],
                figure=fig,
            )
            plotting.plot_surf_roi(
                surf,
                annot,
                hemi=val,
                view="anterior",
                bg_map=sulc,
                bg_on_data=True,
                darkness=1,
                cmap=colormap,
                axes=axs[1, 1],
                figure=fig,
            )
            plotting.plot_surf_roi(
                surf,
                annot,
                hemi=val,
                view="posterior",
                bg_map=sulc,
                bg_on_data=True,
                darkness=1,
                cmap=colormap,
                axes=axs[1, 2],
                figure=fig,
            )

            plt.savefig(
                os.path.join(output_dir, f"{key}_{label}.svg"),
                dpi=300,
                format="svg",
            )
            plt.close()

    imgs = sorted(glob.glob(f"{output_dir}/*svg"))
    return imgs
