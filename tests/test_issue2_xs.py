#******************************************************************************************************
#  test_issue2_xs.py - Gbtc
#
#  Copyright © 2021, Grid Protection Alliance.  All Rights Reserved.
#
#  Licensed to the Grid Protection Alliance (GPA) under one or more contributor license agreements. See
#  the NOTICE file distributed with this work for additional information regarding copyright ownership.
#  The GPA licenses this file to you under the MIT License (MIT), the "License"; you may not use this
#  file except in compliance with the License. You may obtain a copy of the License at:
#
#      http://opensource.org/licenses/MIT
#
#  Unless agreed to in writing, the subject software distributed under the License is distributed on an
#  "AS-IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. Refer to the
#  License for the specific language governing permissions and limitations.
#
#******************************************************************************************************

import inspect
import os
import xml.etree.ElementTree as ET
from configparser import ConfigParser
from datetime import datetime, timedelta, timezone

import numpy as np

from openHistorian.historianConnection import historianConnection
from openHistorian.historianValue import historianValue
from openHistorian.metadataCache import metadataCache
from openHistorian.phasorRecord import phasorRecord
from snapDB.snapClientDatabase import snapClientDatabase
from snapDB.snapConnection import snapConnection
from snapDB.treeStream import treeStream
from oh_gsf import Ticks


REPO_ROOT = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")


def test_host_port_parses_without_indexerror():
    historian = historianConnection("localhost:38402")

    assert historian.hostAddress == "localhost"
    assert historian.port == 38402
    assert historian.HostAddress == "localhost:38402"


def test_host_port_custom_port_and_whitespace():
    historian = historianConnection(" 127.0.0.1 : 12345 ")

    assert historian.hostAddress == "127.0.0.1"
    assert historian.port == 12345


def test_bare_host_uses_default_port():
    historian = historianConnection("localhost")

    assert historian.hostAddress == "localhost"
    assert historian.port == snapConnection.DefaultPort
    assert historian.port == 38402


def test_basekv_returns_basekv_not_sourceindex():
    record = phasorRecord(
        id=10,
        deviceAcronym="TESTDEVICE",
        label="Voltage",
        type="V",
        phase="A",
        sourceIndex=1,
        baseKV=345,
    )

    assert record.BaseKV == 345
    assert record.SourceIndex == 1
    assert record.BaseKV != record.SourceIndex


def test_isdiposed_typo_removed():
    source = inspect.getsource(snapClientDatabase)

    assert "IsDiposed" not in source
    assert "self.reader.IsDisposed" in source
    assert hasattr(treeStream, "IsDisposed")
    assert not hasattr(treeStream, "IsDiposed")


def test_numpy_declared_in_install_requires():
    setup_cfg = os.path.join(REPO_ROOT, "setup.cfg")
    parser = ConfigParser()
    read = parser.read(setup_cfg)

    assert read, f"failed to read {setup_cfg}"
    requires = parser.get("options", "install_requires", fallback="")
    names = {line.strip().split()[0].split(">")[0].split("<")[0].split("=")[0].split("[")[0]
             for line in requires.splitlines() if line.strip()}

    assert "numpy" in names


def _updated_on(text):
    root = ET.fromstring(f"<Record><UpdatedOn>{text}</UpdatedOn></Record>")
    return metadataCache._metadataCache__getUpdatedOn(root)


def test_updated_on_parses_timestamps_without_offset():
    expected = datetime(2026, 1, 15, 8, 30, 0, 120000)

    assert _updated_on("2026-01-15 08:30:00.12") == expected
    assert _updated_on("2026-01-15T08:30:00.120") == expected


def test_updated_on_keeps_utc_offsets():
    assert _updated_on("2026-01-15T08:30:00.12-05:00") == datetime(
        2026, 1, 15, 8, 30, 0, 120000, tzinfo=timezone(-timedelta(hours=5)))
    assert _updated_on("2026-01-15T08:30:00.12+05:30") == datetime(
        2026, 1, 15, 8, 30, 0, 120000, tzinfo=timezone(timedelta(hours=5, minutes=30)))



def test_updated_on_keeps_offset_with_millisecond_fraction():
    assert _updated_on("2026-01-15T08:30:00.120-05:00") == datetime(
        2026, 1, 15, 8, 30, 0, 120000, tzinfo=timezone(-timedelta(hours=5)))

def test_as_quality_keeps_bits_beyond_defined_flags():
    value = historianValue()
    value.Value3 = np.uint64(2**33 + 5)

    assert int(value.AsQuality) == 2**33 + 5
    value.ToString()


def test_ticks_from_datetime_round_trips_microseconds():
    dt = datetime(2026, 9, 1, 12, 34, 56, 789012)

    assert Ticks.ToDateTime(Ticks.FromDateTime(dt)) == dt


def test_ticks_from_timedelta_is_exact_for_long_durations():
    td = timedelta(days=739000, seconds=45296, microseconds=789012)

    assert int(Ticks.FromTimeDelta(td)) == (739000 * 86400 + 45296) * 10000000 + 7890120
