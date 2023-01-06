# vi: set ft=python sts=4 ts=4 sw=4 et:
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
    """
    lut = pd.read_csv(
        os.path.join(freesurfer_home, "FreeSurferLUT.txt"),
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

    # convert subject original T1 to nifit (for FSL)
    convert = MRIConvert(
        in_file=os.path.join(subject_fsdir, "mri", "orig.mgz"),
        out_file=os.path.join(output_dir, "orig.nii.gz"),
        out_type="niigz",
    )
    convert.run()

    # use FSL to convert template file to subject original space
    flirt = FLIRT(
        in_file=pkgrf("fsqa", "data/mni305.cor.nii.gz"),
        reference=os.path.join(output_dir, "orig.nii.gz"),
        out_file=os.path.join(output_dir, "mni2orig.nii.gz"),
        in_matrix_file=os.path.join(output_dir, "inv.xfm"),
        apply_xfm=True,
    )
    flirt.run()

    # use white matter segmentation to compare registrations
    report = SimpleBeforeAfterRPT(
        before=os.path.join(subject_fsdir, "mri", "orig.mgz"),
        after=os.path.join(output_dir, "mni2orig.nii.gz"),
        wm_seg=os.path.join(subject_fsdir, "mri", "wm.mgz"),
        before_label="Subject Orig",
        after_label="Template",
    )
    result = report.run()
    output = result.outputs.out_report

    return output


def get_aseg_plots(subject_fsdir, output_dir, num_imgs):
    colormap = get_colormap()

    # get parcellation and segmentation images
    plotting.plot_roi(
        os.path.join(subject_fsdir, "mri", "aparc+aseg.mgz"),
        os.path.join(subject_fsdir, "mri", "T1.mgz"),
        cmap=colormap,
        display_mode="mosaic",
        dim=-1,
        cut_coords=num_imgs,
        alpha=0.5,
        output_file=os.path.join(output_dir, "aseg.png"),
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
    display.savefig(os.path.join(output_dir, "aparc.png"))
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
            fig, axs = plt.subplots(2, 3, subplot_kw={"project": "3d"})
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
                os.path.join(output_dir, f"{key}_{label}.png"),
                dpi=300,
                format="png",
            )
            plt.close()

    imgs = sorted(glob.glob(f"{output_dir}/*png"))
    return imgs
