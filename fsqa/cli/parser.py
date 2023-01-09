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

"""FSQA Parser"""
# need subjects_dir, freesurfer home, subject, output dir,
# add things for number of slice, etc.?
# add bids stuff too

# import os
from pathlib import Path
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from functools import partial

from .. import config


def _build_parser():
    """Build parser object."""

    def _path_exists(path, parser):
        """Make sure path exists."""
        if path is None or not Path(path).exists():
            raise parser.error(f"Path does not exist: <{path}>")
        return Path(path).expanduser().absolute()

    def _is_file(path, parser):
        """Ensure a given path exists and it is a file."""
        path = _path_exists(path, parser)
        if not path.is_file():
            raise parser.error(
                f"Path should point to a file (or symlink of file): <{path}>."
            )
        return path

    def _drop_sub(participant_label):
        return (
            participant_label[4:]
            if participant_label.startswith("sub-")
            else participant_label
        )

    parser = ArgumentParser(
        description=f"FSQA {config.environment.version} automated "
        "visual reports for FreeSurfer data.",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    PathExists = partial(_path_exists, parser=parser)
    FileExists = partial(_is_file, parser=parser)

    parser.add_argument(
        "--output_dir",
        action="store",
        type=PathExists,
        help="Output path for reports",
    )
    parser.add_argument(
        "--subjects_dir",
        action="store",
        type=PathExists,
        help="FreeSurfer SUBJECTS_DIR",
    )
    parser.add_argument(
        "--participant_label",
        action="store",
        type=_drop_sub,
        help="Participant label identifier. Exclude or use 'all' to generate "
        "reports for all subjects in the subjects directory",
    )
    parser.add_argument(
        "--bids_dir",
        action="store",
        type=PathExists,
        help="Use if data is in BIDS format",
    )
    parser.add_argument(
        "--work_dir",
        "--w",
        action="store",
        type=Path,
        help="Directory for intermediate files.",
    )
    parser.add_argument(
        "--freesurfer_home",
        action="store",
        type=PathExists,
        help="Option to update the FREESURFER_HOME directory.",
    )
    parser.add_argument(
        "--fs_license",
        action="store",
        type=FileExists,
        help="Path to FreeSurfer license.",
    )
    parser.add_argument(
        "--num_imgs",
        action="store",
        type=int,
        help="Number of mosaic images to plot. Default 10.",
    )
    parser.add_argument(
        "--keep",
        action="store_true",
        default=False,
        help="Keep intermediate files used to generate reports. Default False.",
    )

    return parser


def parse_args(args=None, namespace=None):
    """Parse args and run checks on the command line."""
    parser = _build_parser()
    opts = parser.parse_args(args, namespace)

    config.from_dict(vars(opts))
    build_log = config.logger.cli

    # Set up directories
    bids_dir = config.execution.bids_dir
    output_dir = config.execution.output_dir
    work_dir = config.execution.work_dir
    output_layout = config.execution.output_layout

    if config.execution.fs_subjects_dir is None:
        if output_layout == "bids":
            config.execution.fs_subjects_dir = output_dir / "freesurfer"

    if output_dir == bids_dir:
        parser.error(
            "The selected output folder is the same as the input BIDS folder. "
            "Please modify the output path (suggestion: %s)." % bids_dir / "derivatives"
        )

    if bids_dir in work_dir.parents:
        parser.error(
            "The selected working directory is a subdirectory of the input BIDS folder."
            "Please modify the output path."
        )

    config.execution.log_dir = work_dir / config.execution.run_uuid / "logs"
    config.execution.log_dir.mkdir(exist_ok=True, parents=True)

    config.execution.init()
    all_subjects = config.execution.layout.get_subjects()
    if config.execution.participant_label is None or "all":
        config.execution.participant_label = all_subjects
        build_log.info("Running reports for all subjects")

    participant_label = set(config.execution.participant_label)
    missing_subjects = participant_label - set(all_subjects)
    if missing_subjects:
        parser.error(
            "One or more participant labels were not found in the BIDS directory: "
            "%s." % ", ".join(missing_subjects)
        )
    config.execution.participant_label = sorted(participant_label)
    build_log.info(f"FreeSurfer home: {config.execution.freesurfer_home}")

    return opts
