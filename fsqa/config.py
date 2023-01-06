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
Config file for FSQA basic settings.
Handles BIDS data, FreeSurfer environment, etc.
"""
import os
import sys
import logging
from pathlib import Path
from uuid import uuid4
from . import __version__

CONFIG_FILENAME = "fsqa.toml"


class _Config:
    """Abstract config class"""

    _paths = tuple()

    def __init__(self):
        """Avert instantiations"""
        raise RuntimeError("Configuration type is not instantiable.")

    @classmethod
    def load(cls, settings, init=True, ignore=None):
        """Load settings from dictionary"""
        ignore = ignore or {}
        for k, v in settings.items():
            if k in ignore or v is None:
                continue
            if k in cls._paths:
                setattr(cls, k, Path(v).absolute())
            elif hasattr(cls, k):
                setattr(cls, k, v)

        if init:
            try:
                cls.init()
            except AttributeError:
                pass

    @classmethod
    def get(cls):
        """Return defined settings"""
        out = {}
        for k, v in cls.__dict__.items():
            if k.startswith("_") or v is None:
                continue
            if callable(getattr(cls, k)):
                continue
            if k in cls._paths:
                v = str(v)
            out[k] = v

        return out


class environment(_Config):
    """Platform and environment info"""

    exec_env = os.name
    """Execution platform string"""
    version = __version__
    """FSQA version"""


class execution(_Config):
    """FreeSurfer related settings"""

    fs_freesurfer_home = None
    """FreeSurfer Home directory"""
    fs_subjects_dir = None
    """FreeSurfer's subjects directory"""
    fs_license = None
    """FreeSurfer licence file"""
    keep = False
    """Keep intermediate files or not"""
    layout = None
    """A :py:class:`~bids.layout.BIDSLayout` object, see :py:func:`init`."""
    output_dir = None
    """Folder where reports will be stored"""
    output_layout = "bids"
    """Layout of derivatives within output_dir"""
    participant_label = None
    """List of participant ids to be processed"""
    run_uuid = f"{uuid4()}"
    """Run identifier"""
    work_dir = Path("work").absolute()
    """Path to working directory for intermediate files"""

    _layout = None

    _paths = (
        "fs_subjects_dir",
        "layout",
        "output_dir",
        "work_dir",
    )

    @classmethod
    def init(cls, update=False):
        """Create a new BIDS Layout accessible with :attr:`~execution.layout`."""

        if cls._layout is None or update:
            import re
            from bids.layout.index import BIDSLayoutIndexer
            from bids.layout import BIDSLayout

            _db_path = cls.bids_database_dir or (
                cls.work_dir / cls.run_uuid / "bids_db"
            )
            _db_path.mkdir(exist_ok=True, parents=True)

            # Recommended after PyBIDS 12.1
            _indexer = BIDSLayoutIndexer(
                validate=False,
                ignore=(
                    "code",
                    "stimuli",
                    "sourcedata",
                    "models",
                    re.compile(r"^\."),
                    re.compile(
                        r"sub-[a-zA-Z0-9]+(/ses-[a-zA-Z0-9]+)?/(dwi|eeg|ieeg|meg|perf)"
                    ),
                ),
            )
            cls._layout = BIDSLayout(
                str(cls.bids_dir),
                database_path=_db_path,
                reset_database=update,
                indexer=_indexer,
            )
            cls.bids_database_dir = _db_path
        cls.layout = cls._layout
        if cls.bids_filters:
            from bids.layout import Query

            # unserialize pybids Query enum values
            for acq, filters in cls.bids_filters.items():
                cls.bids_filters[acq] = {
                    k: getattr(Query, v[7:-4])
                    if not isinstance(v, Query) and "Query" in v
                    else v
                    for k, v in filters.items()
                }


class loggers:
    """Keep loggers easily accessible (see :py:func:`init`)."""

    _fmt = "%(asctime)s,%(msecs)d %(name)-2s " "%(levelname)-2s:\n\t %(message)s"
    _datefmt = "%y%m%d-%H:%M:%S"

    default = logging.getLogger()
    """root logger"""
    cli = logging.getLogger("cli")
    """Command-line interface logger"""

    @classmethod
    def init(cls):
        """Logger config"""
        _handler = logging.StreamHandler(stream=sys.stdout)
        _handler.setFormatter(logging.Formatter(fmt=cls._fmt, datefmt=cls._datefmt))
        cls.cli.addHandler(_handler)


def from_dict(settings):
    """Read settings from dictionary"""
    execution.load(settings)
    loggers.init()


def load(filename, skip=None):
    """Load settings from file"""
    from toml import loads

    skip = skip or {}
    filename = Path(filename)
    settings = loads(filename.read_text())
    for sectionname, configs in settings.items():
        if sectionname != "environment":
            section = getattr(sys.modules[__name__], sectionname)
            ignore = skip.get(sectionname)
            section.load(configs, ignore=ignore)


def get(flat=False):
    """Get config as dictionary"""
    settings = {
        "environment": environment.get(),
        "execution": execution.get(),
    }
    if not flat:
        return settings

    return {
        ".".join((section, k)): v
        for section, configs in settings.items()
        for k, v in configs.items()
    }


def dumps():
    """Format config into toml."""
    from toml import dumps

    return dumps(get())


def to_filename(filename):
    """Write settings to file."""
    filename = Path(filename)
    filename.write_text(dumps())
