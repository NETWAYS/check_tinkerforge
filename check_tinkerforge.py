#!/usr/bin/env
# COPYRIGHT:
#
# This software is Copyright (c) 2018 NETWAYS GmbH, Matthias Jentsch
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
import os
import time
from functools import partial

from tinkerforge.ip_connection import IPConnection
from tinkerforge.bricklet_temperature import Temperature

__version__ = '0.0.1'

def output(label, state=0, lines=None, perfdata=None, name='Tinkerforge'):
    if lines is None:
        lines = []
    if perfdata is None:
        perfdata = {}

    pluginoutput = name + ': ' + str(label)

    if len(lines):
        pluginoutput += ' - '
        pluginoutput += ' '.join(lines)

    if perfdata:
        pluginoutput += '|'
        pluginoutput += ' '.join(["'" + key + "'" + '=' + str(value) for key, value in perfdata.iteritems()])

    print pluginoutput
    sys.exit(state)

def handle_sigalrm(signum, frame, timeout=None):
    output('CRITICAL - Plugin timed out after %d seconds' % timeout, 2)

class TF(object):
    def __init__(self, host, port, secret, timeout, verbose):
        self.host = host
        self.port = port
        self.secret = secret
        self.timeout = timeout
        self.verbose = verbose
        self.device_type = None
        self.temp = None

        self.type_humidity = "humidity"
        self.type_temperature = "temperature"
        self.type_ptc = "ptc"
        self.type_ambient_light = "ambient_light"

    def connect(self, device_type, uid):
        self.device_type = device_type

        self.ipcon = IPConnection()
        self.ipcon.register_callback(IPConnection.CALLBACK_ENUMERATE, self.cb_enumerate)

        self.ipcon.connect(self.host, self.port)

        if self.verbose:
            print "Connected to host '%s' on port %s." % (self.host, self.port)

        if self.secret:
            try:
                self.ipcon.authenticate(self.secret)
                if self.verbose:
                    print("DEBUG: Authentication succeeded.")
            except:
                output("UNKNOWN - Cannot authenticate", 3)

        self.ipcon.enumerate()

        if self.verbose:
            print "Enumerate request sent."

    def cb_enumerate(self, uid, connected_uid, position, hardware_version, firmware_version, device_identifier, enumeration_type):
        if enumeration_type == IPConnection.ENUMERATION_TYPE_DISCONNECTED:
            return

        if self.verbose:
            print("UID:               " + uid)
            print("Enumeration Type:  " + str(enumeration_type))
            print("Connected UID:     " + connected_uid)
            print("Position:          " + position)
            print("Hardware Version:  " + str(hardware_version))
            print("Firmware Version:  " + str(firmware_version))
            print("Device Identifier: " + str(device_identifier))
            print("")

        # https://www.tinkerforge.com/en/doc/Software/Device_Identifier.html
        # 2113 - Temperature Bricklet 2.0
        # 216 - Temperature Bricklet
        if self.verbose:
            print "DEBUG: Detected device identifier %s" % device_identifier

        if device_identifier == Temperature.DEVICE_IDENTIFIER:
            self.temp = Temperature(uid, self.ipcon)
            self.device_type = self.type_temperature

    def check(self, uid, warning, critical):
        if self.device_type == self.type_temperature:
            ticks = 0
            if uid:
                self.temp = Temperature(uid, self.ipcon)
            else:
                while not self.temp:
                    time.sleep(0.1)
                    ticks = ticks + 1
                    if ticks > self.timeout:
                        output("UNKNOWN - Timeout %s s reached while detecting bricklet. Please use -u to specify the device UID.", 3)

            # Temperature
            temp_value = self.temp.get_temperature() / 100.0
            status = 0

            # TODO: Thresholds, status
            perfdata = {
                "temperature": temp_value
            }

            output("Temperature is %s degrees celcius" % temp_value, status, [], perfdata)

if __name__ == '__main__':
    prog = os.path.basename(sys.argv[0])
    output = partial(output, name=prog)

    parser = argparse.ArgumentParser(prog=prog)
    parser.add_argument('-V', '--version', action='version', version='%(prog)s v' + sys.modules[__name__].__version__)
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-H', '--host', help='The host address of the Tinkerforge device', required=True)
    parser.add_argument("-P", "--port", help="Port (default=4223)", type=int, default=4223)
    parser.add_argument("-S", "--secret", help="Authentication secret")
    parser.add_argument("-u", "--uid", help="UID from Bricklet")
    parser.add_argument("-T", "--type", help="Bricklet type. Supported: 'temperature', 'humidity', 'ambient_light', 'ptc'", required=True)
    parser.add_argument("-w", "--warning", help="Warning threshold")
    parser.add_argument("-c", "--critical", help="Critical threshold")
    parser.add_argument("-t", "--timeout", help="Timeout in seconds", type=int, default=10)
    args = parser.parse_args()

    signal.signal(signal.SIGALRM, partial(handle_sigalrm, timeout=args.timeout))
    signal.alarm(args.timeout)

    tf = TF(args.host, args.port, args.secret, args.timeout, args.verbose)
    tf.connect(args.type, args.uid)

    tf.check(args.uid, args.warning, args.critical)


