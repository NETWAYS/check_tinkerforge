# Icinga Check Plugin for Tinkerforge Bricklets

#### Table of Contents

1. [About](#about)
2. [License](#license)
3. [Support](#support)
4. [Requirements](#requirements)
5. [Installation](#installation)
6. [Run](#run)
7. [Configuration](#configuration)

## About

[Tinkerforge](https://www.tinkerforge.com) allows you to combine bricks and bricklets for your own infrastructure.
This includes sensors for temperature, humidity, PTC and ambient light, etc. in order
to example monitor your datacenter infrastructure.

<img src="https://github.com/NETWAYS/check_tinkerforge/raw/master/doc/images/tinkerforge_bricks.jpg" alt="Tinkerforge Bricks" height="300">
<img src="https://github.com/NETWAYS/check_tinkerforge/raw/master/doc/images/tinkerforge_bricklets.jpg" alt="Tinkerforge Bricks" height="300">

This Icinga plugin allows you to check the following bricklets:

* PTC
* Temperature
* Humidity
* Ambient Light
* Distance IR
* Motion Sensor

Additional features:

* Auto-detect first bricklet from a given type
* Verbose listing of all connected bricklets

## License

This project is licensed under the terms of the GNU General Public License Version 2.

This software is Copyright (c) 2018 by NETWAYS GmbH support@netways.de

## Support

For bugs and feature requests please head over to our [issue tracker](https://github.com/NETWAYS/check_tinkerforge/issues).
You may also send us an email to support@netways.de for general questions or to get technical support.

## Requirements

* Python 2.7+
* `tinkerforge` Python library from Pypi

## Installation

```
pip install tinkerforge
```

Put this plugin into the Icinga PluginDir location.

## Run

```
$ ./check_tinkerforge.py --help
usage: check_tinkerforge.py [-h] [-V] [-v] -H HOST [-P PORT] [-S SECRET]
                            [-u UID] -T TYPE [-w WARNING] [-c CRITICAL]
                            [-t TIMEOUT]

optional arguments:
  -h, --help            show this help message and exit
  -V, --version         show program's version number and exit
  -v, --verbose
  -H HOST, --host HOST  The host address of the Tinkerforge device
  -P PORT, --port PORT  Port (default=4223)
  -S SECRET, --secret SECRET
                        Authentication secret
  -u UID, --uid UID     UID from Bricklet
  -T TYPE, --type TYPE  Bricklet type. Supported: 'temperature', 'humidity',
                        'ambient_light', 'ptc', motion'
  -w WARNING, --warning WARNING
                        Warning threshold. Single value or range, e.g.
                        '20:50'.
  -c CRITICAL, --critical CRITICAL
                        Critical threshold. Single vluae or range, e.g.
                        '25:45'.
  -t TIMEOUT, --timeout TIMEOUT
                        Timeout in seconds
```

### Thresholds

Single thresholds or range based thresholds are supported according to the
Monitoring Plugins API specification.

### Examples

#### PTC

```
check_tinkerforge.py -H 10.0.10.163 -T ptc
OK - Tinkerforge: Temperature is 11.63 degrees celcius|'temperature'=11.63

check_tinkerforge.py -H 10.0.10.163 -T ptc
OK - Tinkerforge: Temperature is 22.43 degrees celcius|'temperature'=22.43
```

#### Temperature

```
check_tinkerforge.py -H 10.0.10.163 -T temperature -w 23
WARNING - Tinkerforge: Temperature is 24.75 degrees celcius|'temperature'=24.75

check_tinkerforge.py -H 10.0.10.163 -T temperature -w 26:55
WARNING - Tinkerforge: Temperature is 24.75 degrees celcius|'temperature'=24.75

check_tinkerforge.py -H 10.0.10.163 -T temperature -w 26:55 -c 30:60
CRITICAL - Tinkerforge: Temperature is 24.75 degrees celcius|'temperature'=24.75

check_tinkerforge.py -H 10.0.10.163 -T temperature -w 23:35
OK - Tinkerforge: Temperature is 24.81 degrees celcius|'temperature'=24.81
```

#### Humidity

```
check_tinkerforge.py -H 10.0.10.163 -T humidity
OK - Tinkerforge: Humidity is 35.4 %HR (Temperature is 26.06 degrees celcius)|'temperature'=26.06 'humidity'=35.4
```

#### Ambient Light

```
check_tinkerforge.py -H 10.0.10.163 -T ambient_light
OK - Tinkerforge: Illuminance is 958.69 lx|'illuminance'=958.69

check_tinkerforge.py -H 10.0.10.163 -T ambient_light -w 900
WARNING - Tinkerforge: Illuminance is 959.41 lx|'illuminance'=959.41
```

#### Distance IR

```
check_tinkerforge.py -H 10.0.10.163 -T distance
OK - Tinkerforge: Distance is 21.6 cm|'distance'=21.6

check_tinkerforge.py -H 10.0.10.163 -T distance -w 50:60
WARNING - Tinkerforge: Distance is 40.1 cm|'distance'=40.1
```

#### Motion Sensor

```
check_tinkerforge.py -H 10.0.10.163 -T motion
OK - Tinkerforge: 

check_tinkerforge.py -H 10.0.10.163 -T distance -w 50:60
WARNING - Tinkerforge: Distance is 40.1 cm|'distance'=40.1
```



## Configuration

An example for Icinga 2 can be found in the [tinkerforge.conf](tinkerforge.conf).
