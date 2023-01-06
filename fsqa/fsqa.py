# vi: set ft=python sts=4 ts=4 sw=4 et:

"""
Main FSQA plotting tools.
"""
import os
import datetime

from .reports import Template, read_report_snippet


def gen_html(output_dir, imgs, out_file, template):
    tlrc = []
    aseg = []
    surf = []

    for img in imgs:
        if "svg" in img:
            tag = read_report_snippet(img)
            tlrc.append(tag)
        elif "aseg" in img or "aparc" in img:
            tag = read_report_snippet(img)
            aseg.append(tag)
        else:
            labels = {
                "lh_pial": "LH Pial",
                "rh_pial": "RH Pial",
                "lh_infl": "LH Inflated",
                "rh_infl": "RH Inflated",
                "lh_white": "LH White Matter",
                "rh_white": "RH White Matter",
            }
            tag = read_report_snippet(img)
            surf_tuple = (labels[os.path.basename(img).split(".")[0]], tag, img)
            surf.append(surf_tuple)

    _config = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d, %H:%M"),
        "subject": os.path.basename(output_dir),
        "tlrc": tlrc,
        "aseg": aseg,
        "surf": surf,
    }

    tpl = Template(template)
    tpl.generate_conf(_config, out_file)

    return out_file
