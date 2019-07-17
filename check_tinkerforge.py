#!/usr/bin/env python
# COPYRIGHT:
#
# This software is Copyright (c) 2018 NETWAYS GmbH, Michael Friedrich
#                                <support@netways.de>
#
# (Except where explicitly superseded by other copyright notices)
#
# LICENSE:
#
# Copyright (C) 2018 NETWAYS GmbH <support@netways.de>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
# or see <http://www.gnu.org/licenses/>.
#
# CONTRIBUTION SUBMISSION POLICY:
#
# (The following paragraph is not intended to limit the rights granted
# to you to modify and distribute this software under the terms of
# the GNU General Public License and is only of importance to you if
# you choose to contribute your changes and enhancements to the
# community by submitting them to NETWAYS GmbH.)
#
# By intentionally submitting any modifications, corrections or
# derivatives to this work, or any other work intended for use with
# this Software, to NETWAYS GmbH, you confirm that
# you are the copyright holder for those contributions and you grant
# NETWAYS GmbH a nonexclusive, worldwide, irrevocable,
# royalty-free, perpetual, license to use, copy, create derivative
# works based on those contributions, and sublicense and distribute
# those contributions and any derivatives thereof.

import argparse
import signal
import sys
import time
from functools import partial

from tinkerforge.ip_connection import IPConnection, Error as IPConnectionError
from tinkerforge.bricklet_ptc_v2 import BrickletPTCV2
from tinkerforge.bricklet_temperature import Temperature
from tinkerforge.bricklet_ambient_light_v2 import BrickletAmbientLightV2
from tinkerforge.bricklet_humidity_v2 import BrickletHumidityV2

__version__ = '0.9.1'

def output(label, state=0, lines=None, perfdata=None, name='Tinkerforge'):
    if lines is None:
        lines = []
    if perfdata is None:
        perfdata = {}

    pluginoutput = ""

    if state == 0:
        pluginoutput += "OK"
    elif state == 1:
        pluginoutput += "WARNING"
    elif state == 2:
        pluginoutput += "CRITICAL"
    elif state == 3:
        pluginoutput += "UNKNOWN"
    else:
        raise RuntimeError("ERROR: State programming error.")

    pluginoutput += " - "

    pluginoutput += name + ': ' + str(label)

    if len(lines):
        pluginoutput += ' - '
        pluginoutput += ' '.join(lines)

    if perfdata:
        pluginoutput += '|'
        pluginoutput += ' '.join(["'" + key + "'" + '=' + str(value) for key, value in perfdata.iteritems()])

    print pluginoutput
    sys.exit(state)


def handle_sigalrm(signum, frame, timeout=None):
    output('Plugin timed out after %d seconds' % timeout, 3)


class TF(object):
    def __init__(self, host, port, secret, timeout, verbose):
        self.host = host
        self.port = port
        self.secret = secret
        self.timeout = timeout
        self.verbose = verbose
        self.device_type = None
        self.ptc = None
        self.temp = None
        self.al = None
        self.hum = None

        self.type_ptc = "ptc"
        self.type_temperature = "temperature"
        self.type_ambient_light = "ambient_light"
        self.type_humidity = "humidity"

        self.ipcon = IPConnection()
        self.ipcon.set_timeout(self.timeout)

    def connect(self, device_type):
        self.device_type = device_type

        self.ipcon.register_callback(IPConnection.CALLBACK_ENUMERATE, self.cb_enumerate)

        self.ipcon.connect(self.host, self.port)

        if self.verbose:
            print "Connected to host '%s' on port %s." % (self.host, self.port)

        if self.secret:
            try:
                self.ipcon.authenticate(self.secret)
                if self.verbose:
                    print("DEBUG: Authentication succeeded.")
            except IPConnectionError:
                output("Cannot authenticate", 3)

        self.ipcon.enumerate()

        if self.verbose:
            print "Enumerate request sent."

    def cb_enumerate(self, uid, connected_uid, position, hardware_version,
                     firmware_version, device_identifier, enumeration_type):
        #ENUMERATION_TYPE_DISCONNECTED
        if enumeration_type == IPConnection.ENUMERATION_TYPE_DISCONNECTED:
            return

        # Note: The order is important, detect PTC before Humidity
        #
        # https://www.tinkerforge.com/en/doc/Software/Bricklets/PTCV2_Bricklet_Python.html
        if device_identifier == BrickletPTCV2.DEVICE_IDENTIFIER:
            self.ptc = BrickletPTCV2(uid, self.ipcon)
            self.device_type = self.type_ptc

        # https://www.tinkerforge.com/en/doc/Software/Bricklets/Temperature_Bricklet_Python.html
        if device_identifier == Temperature.DEVICE_IDENTIFIER:
            self.temp = Temperature(uid, self.ipcon)
            self.device_type = self.type_temperature

        # https://www.tinkerforge.com/en/doc/Software/Bricklets/AmbientLightV2_Bricklet_Python.html
        if device_identifier == BrickletAmbientLightV2.DEVICE_IDENTIFIER:
            self.al = BrickletAmbientLightV2(uid, self.ipcon)
            self.device_type = self.type_ambient_light

        # https://www.tinkerforge.com/en/doc/Software/Bricklets/HumidityV2_Bricklet_Python.html
        if device_identifier == BrickletHumidityV2.DEVICE_IDENTIFIER:
            self.hum = BrickletHumidityV2(uid, self.ipcon)
            self.device_type = self.type_humidity

        if self.verbose:
            print("UID:               " + uid)
            print("Enumeration Type:  " + str(enumeration_type))
            print("Connected UID:     " + connected_uid)
            print("Position:          " + position)
            print("Hardware Version:  " + str(hardware_version))
            print("Firmware Version:  " + str(firmware_version))
            print("Device Identifier: " + str(device_identifier))
            print("Device Type:       " + str(self.device_type))
            print("")

    @staticmethod
    def parse_threshold(t):
        # ranges
        if ":" in t:
            return t.split(":")
        else:
            return [t]

    def eval_threshold_generic(self, val, threshold):
        t_arr = self.parse_threshold(threshold)

        # if we only have one value, treat this as 0..value range
        if len(t_arr) == 1:
            if self.verbose:
                print "Evaluating thresholds, single %s on value %s" % (" ".join(t_arr), val)

            if val > (float(t_arr[0])):
                return True
        else:
            if self.verbose:
                print "Evaluating thresholds, rangle %s on value %s" % (":".join(t_arr), val)

            if val < float(t_arr[0]) or val > float(t_arr[1]):
                return True

        return False

    def eval_thresholds(self, val, warning, critical):
        status = 0

        if warning:
            if self.eval_threshold_generic(val, warning):
                status = 1

        if critical:
            if self.eval_threshold_generic(val, critical):
                status = 2

        return status

    def check(self, uid, warning, critical):
        # PTC
        # https://www.tinkerforge.com/en/doc/Software/Bricklets/PTCV2_Bricklet_Python.html
        if self.device_type == self.type_ptc:
            ticks = 0
            if uid:
                self.ptc = BrickletPTCV2(uid, self.ipcon)
            else:
                # TODO: refactor
                while not self.ptc:
                    time.sleep(0.1)
                    ticks = ticks + 1
                    if ticks > self.timeout * 10:
                        output("Timeout %s s reached while detecting bricklet. "
                               "Please use -u to specify the device UID." % self.timeout, 3)

            ptc_value = self.ptc.get_temperature() / 100.0

            status = self.eval_thresholds(ptc_value, warning, critical)

            perfdata = {
                "temperature": ptc_value
            }
            output("Temperature is %s degrees celcius" % ptc_value, status, [], perfdata)

        # Temperature
        # https://www.tinkerforge.com/en/doc/Software/Bricklets/Temperature_Bricklet_Python.html
        if self.device_type == self.type_temperature:
            ticks = 0
            if uid:
                self.temp = Temperature(uid, self.ipcon)
            else:
                # TODO: refactor
                while not self.temp:
                    time.sleep(0.1)
                    ticks = ticks + 1
                    if ticks > self.timeout * 10:
                        output("Timeout %s s reached while detecting bricklet. "
                               "Please use -u to specify the device UID." % self.timeout, 3)

            temp_value = self.temp.get_temperature() / 100.0

            status = self.eval_thresholds(temp_value, warning, critical)

            perfdata = {
                "temperature": temp_value
            }

            output("Temperature is %s degrees celcius" % temp_value, status, [], perfdata)

        # Ambient Light
        # https://www.tinkerforge.com/en/doc/Software/Bricklets/AmbientLightV2_Bricklet_Python.html
        if self.device_type == self.type_ambient_light:
            ticks = 0
            if uid:
                self.al = BrickletAmbientLightV2(uid, self.ipcon)
            else:
                # TODO: refactor
                while not self.al:
                    time.sleep(0.1)
                    ticks = ticks + 1
                    if ticks > self.timeout * 10:
                        output("Timeout %s s reached while detecting bricklet. "
                               "Please use -u to specify the device UID." % self.timeout, 3)

            al_value = self.al.get_illuminance() / 100.0

            status = self.eval_thresholds(al_value, warning, critical)

            perfdata = {
                "illuminance": al_value
            }

            output("Illuminance is %s lx" % al_value, status, [], perfdata)

        # Humidity
        # https://www.tinkerforge.com/en/doc/Software/Bricklets/HumidityV2_Bricklet_Python.html
        if self.device_type == self.type_humidity:
            ticks = 0
            if uid:
                self.hum = BrickletHumidityV2(uid, self.ipcon)
            else:
                # TODO: refactor
                while not self.hum:
                    time.sleep(0.1)
                    ticks = ticks + 1
                    if ticks > self.timeout * 10:
                        output("Timeout %s s reached while detecting bricklet. "
                               "Please use -u to specify the device UID." % self.timeout, 3)

            hum_value = self.hum.get_humidity() / 100.0
            hum_temp_value = self.hum.get_temperature() / 100.0

            status = self.eval_thresholds(hum_value, warning, critical)

            perfdata = {
                "humidity": hum_value,
                "temperature": hum_temp_value
            }

            output("Humidity is %s %%HR (Temperature is %s degrees celcius)" % (hum_value, hum_temp_value),
                   status, [], perfdata)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-V', '--version', action='version', version='%(prog)s v' + sys.modules[__name__].__version__)
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-H', '--host', help='The host address of the Tinkerforge device', required=True)
    parser.add_argument("-P", "--port", help="Port (default=4223)", type=int, default=4223)
    parser.add_argument("-S", "--secret", help="Authentication secret")
    parser.add_argument("-u", "--uid", help="UID from Bricklet")
    parser.add_argument("-T", "--type", required=True,
                        help="Bricklet type. Supported: 'temperature', 'humidity', 'ambient_light', 'ptc'")
    parser.add_argument("-w", "--warning", help="Warning threshold. Single value or range, e.g. '20:50'.")
    parser.add_argument("-c", "--critical", help="Critical threshold. Single vluae or range, e.g. '25:45'.")
    parser.add_argument("-t", "--timeout", help="Timeout in seconds (default 10s)", type=int, default=10)
    args = parser.parse_args()

    signal.signal(signal.SIGALRM, partial(handle_sigalrm, timeout=args.timeout))
    signal.alarm(args.timeout)

    tf = TF(args.host, args.port, args.secret, args.timeout, args.verbose)
    tf.connect(args.type)

    tf.check(args.uid, args.warning, args.critical)
