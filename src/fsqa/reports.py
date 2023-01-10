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
import base64
import re

from nipype.utils.filemanip import split_filename


class Template(object):
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


def read_report_snippet(in_file):
    """
    Add an image snippet into the report.
    Modified from nipreps under Apache 2 license.
    """

    _, _, ext = split_filename(in_file)
    with open(in_file) as img_file:
        if "svg" in ext:
            svg_tag_line = 0
            content = img_file.read().split("\n")
            corrected = []
            for idx, line in enumerate(content):
                if "<svg" in line:
                    line = re.sub(' height="[0-9.]+[a-z]*"', "", line)
                    line = re.sub(' width="[0-9.]+[a-z]*"', "", line)
                    if svg_tag_line == 0:
                        svg_tag_line = idx
                corrected.append(line)
            return "\n".join(corrected[svg_tag_line:])
        elif "png" in ext:
            png_uri = base64.b64encode(open(img_file, "rb").read()).decode("utf-8")
            png_tag = "<img src='data:image/png;base64,{0}'>".format(png_uri)
            return "\n".join(png_tag)


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


def cleanup(subject_dir):
    file_exts = [".svg", ".png", ".xfm", ".nii.gz"]
    for root, _, files in os.walk(subject_dir):
        for ff in files:
            if ff.endswith([ext for ext in file_exts]):
                os.remove(os.path.join(root, ff))

    return
