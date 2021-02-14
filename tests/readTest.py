#******************************************************************************************************
#  readTest.py - Gbtc
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
#  Code Modification History:
#  ----------------------------------------------------------------------------------------------------
#  02/14/2021 - J. Ritchie Carroll
#       Generated original version of source code.
#
#******************************************************************************************************

import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../src")

from openHistorian.historianConnection import historianConnection
from openHistorian.historianInstance import historianInstance
from openHistorian.historianKey import historianKey
from openHistorian.historianValue import historianValue
from openHistorian.metadataCache import metadataCache
from openHistorian.measurementRecord import SignalType
from snapDB.timestampSeekFilter import timestampSeekFilter
from snapDB.pointIDMatchFilter import pointIDMatchFilter
from typing import Optional, List
from datetime import datetime, timedelta
from time import time
import numpy as np

def readTest():
    # Create historian connection (the root API object)
    historian = historianConnection("localhost")
    instance: Optional[historianInstance] = None

    try:
        print("Connecting to openHistorian...")
        historian.Connect()

        if not historian.IsConnected or len(historian.InstanceNames) == 0:
            print("No openHistorian instances detected!")
        else:
            # Get first historian instance
            initialInstance = historian.InstanceNames[0]
        
            print(f"Opening \"{initialInstance}\" database instance...")
            instance = historian.OpenInstance(initialInstance)
                
            # Get a reference to the openHistorian metadata cache
            historian.RefreshMetadata()
            metadata = historian.Metadata

            # Lookup measurements that represent frequency values
            records = metadata.GetMeasurementsBySignalType(SignalType.FREQ, instance.Name)
            recordCount = len(records)

            print(f"Queried {recordCount:,} metadata records associated with \"{instance.Name}\" database instance.")

            if recordCount > 0:
                pointIDList = metadataCache.ToPointIDList(records)

                # Execute a test read for data archived ten seconds ago
                endTime = datetime.utcnow() - timedelta(seconds = 10)
                startTime = endTime - timedelta(milliseconds = 33)
                    
                print(f"Starting read for {len(pointIDList):,} points from {startTime} to {endTime}...\r\n")
                    
                TestRead(instance, historian.Metadata, startTime, endTime, pointIDList)
    except Exception as ex:
        print(f"Failed to connect: {ex}")
    finally:
        if instance is not None:
            instance.Dispose()

        if historian.IsConnected:
            print("Disconnecting from openHistorian")
        
        historian.Disconnect()

def TestRead(instance: historianInstance, metadata: metadataCache, startTime: datetime, endTime: datetime, pointIDList: List[np.uint64]):
    timeFilter = timestampSeekFilter.CreateFromRange(startTime, endTime)
    pointFilter = pointIDMatchFilter.CreateFromList(pointIDList)

    opStart = time()
    reader = instance.Read(timeFilter, pointFilter)
    count = 0
                
    key = historianKey()
    value = historianValue()

    while reader.Read(key, value):
        count += 1
        print(f"    Point {key.ToString(metadata)} = {value.ToString()}")

    print(f"\r\nRead complete for {count:,} points in {(time() - opStart):.2f} seconds.\r\n")

if __name__ == "__main__":
    readTest()
