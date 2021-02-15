<!--- Do not make this image location relative, README.md in root is a symbolic reference to one in docs. See CreateReadMeSymLink.cmd for more information. --->
![Logo](https://raw.githubusercontent.com/GridProtectionAlliance/openhistorian-python/main/docs/img/PythonAPI_75.png)

![CodeQL](https://github.com/GridProtectionAlliance/openhistorian-python/workflows/CodeQL/badge.svg)

The openHistorian Python API is used for high-speed reading and writing of time-series data with the openHistorian.

The openHistorian is an open source system designed to efficiently integrate and archive process control data, e.g., SCADA, synchrophasor, digital fault recorder or any other time-series data used to support process operations. The openHistorian is optimized to store and retrieve large volumes of time-series data quickly and efficiently, including high-resolution sub-second information that is measured very rapidly, e.g., many thousands of times per second. See [2-page pdf flyer](https://gridprotectionalliance.org/docs/products/openhistorian/OpenHistorian2018.pdf).

# Overview
The openHistorian 2 is built using the [SNAPdb Engine](http://www.gridprotectionalliance.org/technology.asp#SnapDB) - a key/value pair archiving technology. SNAPdb was developed to significantly improve the ability to handle extremely large volumes of real-time streaming data and directly serve the data to consuming applications and systems. See the Python API implementation of [SNAPdb](https://github.com/GridProtectionAlliance/openhistorian-python/tree/main/src/snapDB).

Through use of the [SNAPdb Engine](http://www.gridprotectionalliance.org/technology.asp#SnapDB), the openHistorian inherits very fast performance with very low lag-time for data insertion. The openHistorian 2 is a time-series implementation of the SNABdb engine where the "[key](https://github.com/GridProtectionAlliance/openhistorian-python/tree/main/src/openHistorian/historianKey.py)" is a tuple of time and measurement ID, and the "[value](https://github.com/GridProtectionAlliance/openhistorian-python/tree/main/src/openHistorian/historianValue.py)" is the stored data - which can be most any data type and associated flags. See the Python API implementation of the [openHistorian instance of SNAPdb](https://github.com/GridProtectionAlliance/openhistorian-python/tree/main/src/openHistorian)

The Python API for openHistorian is designed as a socket-based, high-speed API that interacts directly with the openHistorian in-memory cache for very high speed extraction of near real-time data. The archive files produced by the openHistorian are [ACID Compliant](https://en.wikipedia.org/wiki/ACID) which create a very durable and consistent file structure that is resistant to data corruption. Internally the data structure is based on a [B+ Tree](https://en.wikipedia.org/wiki/B%2B_tree) that allows out-of-order data insertion.

## Example Usage
Full source for the following two usage examples can be found here:
* Reading Data ([readTest.py](https://github.com/GridProtectionAlliance/openhistorian-python/blob/main/tests/readTest.py))
* Writing Data ([writeTest.py](https://github.com/GridProtectionAlliance/openhistorian-python/blob/main/tests/writeTest.py))

### Reading Data
The following example shows how to establish a connection to the openHistorian, open a client database instance, refresh available metadata, filter metadata to desired set of signal types, establish a start and stop time for the read, then read each time-series values as a historian [key](https://github.com/GridProtectionAlliance/openhistorian-python/tree/main/src/openHistorian/historianKey.py) / [value](https://github.com/GridProtectionAlliance/openhistorian-python/tree/main/src/openHistorian/historianValue.py) pair.

```python
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
```

### Writing data
The following example shows how to establish a connection to the openHistorian, open a client database instance, build a new time-series value historian [key](https://github.com/GridProtectionAlliance/openhistorian-python/tree/main/src/openHistorian/historianKey.py) / [value](https://github.com/GridProtectionAlliance/openhistorian-python/tree/main/src/openHistorian/historianValue.py) pair, then write the data to the openHistorian.
```python
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
```

# License
openHistorian and the Python API are licensed under the [MIT License](https://opensource.org/licenses/MIT).
