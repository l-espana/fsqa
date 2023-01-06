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

    parser.add_argument(
        "--output_dir",
        action="store",
        type=PathExists,
        help="the output path for reports",
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
        help="Participant label identifier. Use 'all' to generate "
        "reports for all subjects in the subjects directory",
    )
    parser.add_argument(
        "--bids",
        action="store_true",
        default=False,
        help="assume data and outputs are not BIDS formatted",
    )

    return parser


def parse_args(args=None, namespace=None):
    """Parse args and run checks on the command line."""
    parser = _build_parser()
    opts = parser.parse_args(args, namespace)

    config.from_dict(vars(opts))
    # build_log = config.logger.cli

    # Set up directories
    output_dir = config.execution.output_dir
    # work_dir = config.execution.work_dir
    output_layout = config.execution.output_layout

    if config.execution.fs_subjects_dir is None:
        if output_layout == "bids":
            config.execution.fs_subjects_dir = output_dir / "freesurfer"
