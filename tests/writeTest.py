#******************************************************************************************************
#  writeTest.py - Gbtc
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
from snapDB.enumerations import QualityFlags
from gsf import Ticks
from typing import Optional
from datetime import datetime
import numpy as np

def writeTest():
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
                
            key = historianKey()
            key.PointID = 1
            key.Timestamp = Ticks.FromDateTime(datetime.utcnow())

            value = historianValue()
            value.AsSingle = np.float32(1000.98)
            value.AsQuality = QualityFlags.WARNINGHIGH

            print("Writing test point...")
            instance.Write(key, value)
    except Exception as ex:
        print(f"Failed to connect: {ex}")
    finally:
        if instance is not None:
            instance.Dispose()

        if historian.IsConnected:
            print("Disconnecting from openHistorian")
        
        historian.Disconnect()

if __name__ == "__main__":
    writeTest()
