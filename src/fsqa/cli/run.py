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
Main workflow.
"""
import os
from pathlib import Path
from pkg_resources import resource_filename as pkgrf
from niworkflows.utils.bids import collect_participants
from fsqa.cli.parser import parse_args
from fsqa import config
from fsqa.freesurfer import check_reconall, get_tlrc_report, get_aseg_plots
from fsqa.reports import gen_html, cleanup


def main():
    """Entry point."""
    parse_args()
    template = Path(pkgrf("fsqa.data", "individual.html"))
    pwd = os.getcwd()

    # Initial setup and config
    config_file = (
        config.execution.work_dir / config.execution.run_uuid / "fsqa.config.toml"
    )
    config_file.parent.mkdir(exist_ok=True, parents=True)
    config.to_filename(config_file)
    config.load(config_file)
    os.environ["FREESURFER_HOME"] = config.execution.freesurfer_home
    logger = config.loggers.workflow

    # Initialize subjects and verify freesurfer output
    # BIDS or not?
    subject_list = collect_participants(
        config.execution.layout, participant_label=config.execution.participant_label
    )
    if not subject_list:
        subject_list = [direc for _, direc, _ in os.walk(config.execution.subjects_dir)]

    for subject_id in subject_list:
        if not check_reconall(config.execution.subjects_dir / subject_id):
            subject_list.remove(subject_id)
            logger.info(f">> {subject_id} recon-all did not complete, skipping!")

    # Actual workflow
    for subject_id in subject_list:
        logger.info(f">> Generating report for {subject_id}")
        work_dir = config.execution.work_dir / subject_id
        work_dir.mkdir(exist_ok=True)
        os.chdir(work_dir)

        out_file = config.execution.output_dir / f"sub-{subject_id}.html"
        tlrc_svg = [
            get_tlrc_report(
                config.execution.subjects_dir / subject_id,
                config.execution.output_dir / subject_id,
            )
        ]
        aseg_imgs = get_aseg_plots(
            config.execution.freesurfer_home,
            config.execution.subjects_dir / subject_id,
            config.execution.output_dir / subject_id,
            num_imgs=config.execution.num_imgs,
        )
        in_plots = tlrc_svg + aseg_imgs
        gen_html(config.execution.output_dir / subject_id, in_plots, out_file, template)

        if not config.execution.keep:
            cleanup(config.execution.output_dir / subject_id)

    os.chdir(pwd)
    logger.info(">> FSQA workflow complete!")


if __name__ == "__main__":
    raise RuntimeError("fsqa/cli/run.py should not be run directly\n")
