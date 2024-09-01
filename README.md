# Power-Mate PM10AHDS Serial Interface Library
A very bare-bones python class to interface to a [Power-Mate PM10AHDS Power Monitor](https://www.cabac.com.au/pm10ahds) via RS232.


## Physical Interfaces
* RJ45 connector on unit, pinout TBD. Interface cable should be available from Cabac soon.
* RS232 levels, 9600 baud 8N1.

## Supported Commands
* Status - Request the current status registers, which includes accumulated energy, and instantaneous voltage, power, current and powerfactor.
* Erase - Resets all registers. The meter will start collecting data again after the erase occurs.

## Pre-Requisites
This class just requires the pyserial library, which can be installed from a package manager (e.g. `apt-get install python3-serial`), or in a virtualenv using pip:

```console
python3 -m venv venv
pip install -r requirements.txt
```

## Example Usage
```
Python 3.9.18 (main, Aug 24 2023, 21:20:15) 
[Clang 14.0.0 (clang-1400.0.29.202)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>> from PM10AHDS import PM10AHDS
>>> power_meter = PM10AHDS('/dev/tty.usbserial-AU05RDD6')
>>> power_meter.request_status()
{'runtime_seconds': 12629417, 'energy_kwh': 24.92328723194464, 'power_w': 3.2, 'voltage_v': 246.436, 'current_a': 0.0314, 'powerfactor_leadlag': 'lag', 'powerfactor': 0.41321, 'apparent_power_va': 7.747}
>>> power_meter.request_erase()
True
>>> power_meter.request_status()
{'runtime_seconds': 21, 'energy_kwh': 1.8768055555555704e-05, 'power_w': 3.25, 'voltage_v': 246.328, 'current_a': 0.0323, 'powerfactor_leadlag': 'lag', 'powerfactor': 0.40837, 'apparent_power_va': 7.962}
```

There is also a test script available which just polls for the latest status:
```
% python PM10AHDS.py /dev/tty.usbserial-AU05RDD6
2024-09-01 12:03:55,766 INFO:Attempting to connect to a PM10AHDS on /dev/tty.usbserial-AU05RDD6, at 9600 baud...
2024-09-01 12:03:55,771 DEBUG:Sending Status Request: b'<01S,;00E0\r\n'
2024-09-01 12:03:57,995 DEBUG:Status Response: b'>01S,0,0,12629320,89723519413,3200,246572000,31500,1,412700,7767;0C6B\r'
{'apparent_power_va': 7.767,
 'current_a': 0.0315,
 'energy_kwh': 24.923199836944644,
 'power_w': 3.2,
 'powerfactor': 0.4127,
 'powerfactor_leadlag': 'lag',
 'runtime_seconds': 12629320,
 'voltage_v': 246.572}
```