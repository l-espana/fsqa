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
