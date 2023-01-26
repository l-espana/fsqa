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
Utility class for generating a config file from a jinja template.
https://github.com/oesteban/endofday/blob/f2e79c625d648ef45b08cc1f11fd0bd84342d604/endofday/core/template.py

Along with other report-related functions.
"""
import os
import datetime
import jinja2

# import base64

# from nipype.utils.filemanip import split_filename


class Template(object):
    """Simplified jinja2 template class from oesteban."""

    def __init__(self, template_str):
        self.template_str = template_str
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(searchpath="/"),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def compile(self, configs):
        """Generates a string with the replacements"""
        template = self.env.get_template(self.template_str)
        return template.render(configs)

    def generate_conf(self, configs, path):
        """Saves the outcome after replacement on the template to file"""
        output = self.compile(configs)
        with open(path, "w+") as output_file:
            output_file.write(output)


def read_img_data(in_file):
    """
    Add an image snippet into the report.
    Modified from nipreps/mriqc/reports/utils.py under Apache 2 license
    to include PNG support.

    Parameters
    ----------
    in_file : path or str representing path to image file
        Image file to include in html report.

    Returns
    -------
    str
        Tag generated from the image that can be inserted
        in the html report.
    """

    """
    if "svg" in ext:
        svg_uri = base64.b64encode(open(in_file, "rb").read()).decode("utf-8")
        svg_tag = "<img src='data:image/svg+xml;base64,{0}'>".format(str(svg_uri))
        return "\n".join(svg_tag)
    if "png" in ext:
        png_uri = base64.b64encode(open(in_file, "rb").read()).decode("utf-8")
        png_tag = "<img src='data:image/png;base64,{0}'>".format(str(png_uri))
        return "\n".join(png_tag)
    """
    # _, _, ext = split_filename(in_file)
    with open(in_file) as img_file:
        return img_file.read()


def gen_html(output_dir, imgs, out_file, template):
    """Generates the html report file given a set of images
    and the html template to use.

    Parameters
    ----------
    output_dir : path or str representing a path to a directory
        HTML output directory.
    imgs : list
        List of SVG/PNG string tags to be input in html report.
    out_file : str
        File name for the html report.
    template : class::Template
        Jinja2 template to be used for html report.

    Returns
    -------
    out_file : str or path representing a file
        HTML report file path.
    """
    tlrc = []
    aseg = []
    surf = []

    for img in imgs:
        if "tlrc" in img:
            tag = read_img_data(img)
            tlrc.append(tag)
        elif "aseg" in img or "aparc" in img:
            tag = read_img_data(img)
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
            tag = read_img_data(img)
            surf_tuple = (labels[os.path.basename(img).split(".")[0]], tag)
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


def cleanup(subject_dir):
    """Function to remove intermediate files if indicated.

    Parameters
    ----------
    subject_dir : path or str representing path to a directory
        Working subject directory where intermediate files are put.
    """
    file_exts = [".svg", ".xfm", ".nii.gz", ".mat"]
    for root, _, files in os.walk(subject_dir):
        for ff in files:
            for ext in file_exts:
                if ff.endswith(ext) and ff != "mni305.cor.nii.gz":
                    os.remove(os.path.join(root, ff))

    return
