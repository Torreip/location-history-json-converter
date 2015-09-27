#!/usr/bin/env python

# Copyright 2012 Gerwin Sturm, FoldedSoft e.U. / www.foldedsoft.at
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

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
# from __future__ import unicode_literals

import sys
import os
import json
import math
import logging
import time

from argparse import ArgumentParser
from datetime import datetime

logger = logging.getLogger(__name__)


class loc_hist_parser():

    def __init__(self, in_file=None, out_file=None):
        self.data = None
        self.in_file = None
        self.out_file = None

    def open_in_json(self, in_file):
        if not os.path.exists(in_file):
            logger.error('Invalid input file: {}'.format(in_file))
            raise ValueError
        else:
            self.in_file = os.path.abspath(in_file)

        try:
            logger.debug('* Opening JSON')
            json_data = open(self.in_file).read()
        except BaseException:
            logging.exception("Error opening input file")
            sys.exit()

        try:
            logger.debug('* Decoding JSON')
            self.data = json.loads(json_data)
        except BaseException:
            logging.exception("Error decoding json")
            sys.exit()

#         print(self.data)
        l = len(self.data["locations"])
        if "locations" in self.data and l > 0:
            logger.debug('=> Successfully decoded {} items.'.format(l))
        else:
            logger.error('=> JSON decoding gave no results.')

    def truncate_time_interval(self, start_time, end_time='Now'):
        logger.debug('* Cut time interval.')

        if end_time == 'Now':
            end_time = time.time()

        out_dat = []

        while len(self.data[u'locations']) > 0:
            item = self.data[u'locations'].pop()

            ts = int(item[u'timestampMs'])
            ms = ts % 1000
            ts //= 1000
            if start_time <= ts <= end_time:
                out_dat.append(item)

        self.data[u'locations'] = out_dat

    def check_out_file(self, out_file):
        if os.path.exists(out_file):
            logger.warning('Output file already exists, overwritting: {}'.format(out_file))
        self.out_file = os.path.abspath(out_file)

        if self.in_file == self.out_file:
            logger.error("Input and output have to be different files")
            sys.exit()

    def export_to_json(self, out_file, js_var=None):
        self.check_out_file(out_file)
        f_out = open(self.out_file, "w")
        items = self.data["locations"]

        if js_var is not None:
            f_out.write("window.%s = " % js_var)

        f_out.write("{\n")
        f_out.write("  \"data\": {\n")
        f_out.write("    \"items\": [\n")
        first = True

        for item in items:
            if first:
                first = False
            else:
                f_out.write(",\n")
            f_out.write("      {\n")
            f_out.write("         \"timestampMs\": %s,\n" % item["timestampMs"])
            f_out.write("         \"latitude\": %s,\n" % (item["latitudeE7"] / 10000000))
            f_out.write("         \"longitude\": %s\n" % (item["longitudeE7"] / 10000000))
            f_out.write("      }")
        f_out.write("\n    ]\n")
        f_out.write("  }\n}")
        if js_var is not None:
            f_out.write(";")
        f_out.close()
        logger.debug('=> Wrote {} places in {}'.format(len(items),
                                                       self.out_file))

    def export_to_json_raw(self, out_file):
        self.check_out_file(out_file)
        f_out = open(self.out_file, "w")
        f_out.write(json.dumps(self.data))
        f_out.close()
        logger.debug('=> Wrote {} places in {}'.format(len(self.data["locations"]),
                                                       self.out_file))


    def export_to_csv(self, out_file):
        self.check_out_file(out_file)
        f_out = open(self.out_file, "w")
        items = self.data["locations"]

        f_out.write("Time,Location\n")
        for item in items:
            f_out.write(datetime.fromtimestamp(int(item["timestampMs"]) / 1000).strftime("%Y-%m-%d %H:%M:%S"))
            f_out.write(",")
            f_out.write("%s %s\n" % (item["latitudeE7"] / 10000000, item["longitudeE7"] / 10000000))
        f_out.close()
        logger.debug('=> Wrote {}'.format(self.out_file))

    def export_to_kml(self, out_file):
        self.check_out_file(out_file)
        f_out = open(self.out_file, "w")
        items = self.data["locations"]

        f_out.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
        f_out.write("<kml xmlns=\"http://www.opengis.net/kml/2.2\">\n")
        f_out.write("  <Document>\n")
        f_out.write("    <name>Location History</name>\n")
        for item in items:
            f_out.write("    <Placemark>\n")
            # Order of these tags is important to make valid KML: TimeStamp,
            # ExtendedData, then Point
            f_out.write("      <TimeStamp><when>")
            f_out.write(datetime.fromtimestamp(int(item["timestampMs"]) / 1000).strftime("%Y-%m-%dT%H:%M:%SZ"))
            f_out.write("</when></TimeStamp>\n")
            if "accuracy" in item or "speed" in item or "altitude" in item:
                f_out.write("      <ExtendedData>\n")
                if "accuracy" in item:
                    f_out.write("        <Data name=\"accuracy\">\n")
                    f_out.write("          <value>%d</value>\n" % item["accuracy"])
                    f_out.write("        </Data>\n")
                if "speed" in item:
                    f_out.write("        <Data name=\"speed\">\n")
                    f_out.write("          <value>%d</value>\n" % item["speed"])
                    f_out.write("        </Data>\n")
                if "altitude" in item:
                    f_out.write("        <Data name=\"altitude\">\n")
                    f_out.write("          <value>%d</value>\n" % item["altitude"])
                    f_out.write("        </Data>\n")
                f_out.write("      </ExtendedData>\n")
            f_out.write("      <Point><coordinates>%s,%s</coordinates></Point>\n" % (item["longitudeE7"] / 10000000, item["latitudeE7"] / 10000000))
            f_out.write("    </Placemark>\n")
        f_out.write("  </Document>\n</kml>\n")
        f_out.close()
        logger.debug('=> Wrote {}'.format(self.out_file))

    def export_to_gpx(self, out_file, gpx_tracks=False):
        self.check_out_file(out_file)
        f_out = open(self.out_file, "w")
        items = self.data["locations"]

        f_out.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
        f_out.write(("<gpx xmlns=\"http://www.topografix.com/GPX/1/1\" "
                     "version=\"1.1\" "
                     "creator=\"Google Latitude JSON Converter\" "
                     "xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" "
                     "xsi:schemaLocation=\"http://www.topografix.com/GPX/1/1 "
                     "http://www.topografix.com/GPX/1/1/gpx.xsd\">\n"))
        f_out.write("  <metadata>\n")
        f_out.write("    <name>Location History</name>\n")
        f_out.write("  </metadata>\n")
        if not gpx_tracks:
            for item in items:
                f_out.write("  <wpt lat=\"%s\" lon=\"%s\">\n" %
                    (item["latitudeE7"] / 10000000,
                     item["longitudeE7"] / 10000000))
                if "altitude" in item:
                    f_out.write("    <ele>%d</ele>\n" % item["altitude"])
                f_out.write("    <time>%s</time>\n" % str(datetime.fromtimestamp(int(item["timestampMs"]) / 1000).strftime("%Y-%m-%dT%H:%M:%SZ")))
                f_out.write("    <desc>%s" % datetime.fromtimestamp(int(item["timestampMs"]) / 1000).strftime("%Y-%m-%d %H:%M:%S"))
                if "accuracy" in item or "speed" in item:
                    f_out.write(" (")
                    if "accuracy" in item:
                        f_out.write("Accuracy: %d" % item["accuracy"])
                    if "accuracy" in item and "speed" in item:
                        f_out.write(", ")
                    if "speed" in item:
                        f_out.write("Speed:%d" % item["speed"])
                    f_out.write(")")
                f_out.write("</desc>\n")
                f_out.write("  </wpt>\n")
        elif gpx_tracks:
            f_out.write("  <trk>\n")
            f_out.write("    <trkseg>\n")
            lastloc = None
            # The deltas below assume input is in reverse chronological order.  If it's not, uncomment this:
            # items = sorted(data["data"]["items"], key=lambda x: x['timestampMs'], reverse=True)
            for item in items:
                if lastloc:
                    timedelta = -((int(item['timestampMs']) - int(lastloc['timestampMs'])) / 1000 / 60)
                    distancedelta = getDistanceFromLatLonInKm(item['latitudeE7'] / 10000000, item['longitudeE7'] / 10000000, lastloc['latitudeE7'] / 10000000, lastloc['longitudeE7'] / 10000000)
                    if timedelta > 10 or distancedelta > 40:
                        # No points for 10 minutes or 40km in under 10m? Start
                        # a new track.
                        f_out.write("    </trkseg>\n")
                        f_out.write("  </trk>\n")
                        f_out.write("  <trk>\n")
                        f_out.write("    <trkseg>\n")
                f_out.write("      <trkpt lat=\"%s\" lon=\"%s\">\n" % (item["latitudeE7"] / 10000000, item["longitudeE7"] / 10000000))
                if "altitude" in item:
                    f_out.write("        <ele>%d</ele>\n" % item["altitude"])
                f_out.write("        <time>%s</time>\n" % str(datetime.fromtimestamp(int(item["timestampMs"]) / 1000).strftime("%Y-%m-%dT%H:%M:%SZ")))
                if "accuracy" in item or "speed" in item:
                    f_out.write("        <desc>\n")
                    if "accuracy" in item:
                        f_out.write("          Accuracy: %d\n" % item["accuracy"])
                    if "speed" in item:
                        f_out.write("          Speed:%d\n" % item["speed"])
                    f_out.write("        </desc>\n")
                f_out.write("      </trkpt>\n")
                lastloc = item
            f_out.write("    </trkseg>\n")
            f_out.write("  </trk>\n")
        else:
            logger.error('Error, should never be reached.')
        f_out.write("</gpx>\n")
        f_out.close()
        logger.debug('=> Wrote {}'.format(self.out_file))


def main(argv):
    logging.basicConfig(level=logging.DEBUG,
                        format='%(message)s')

    arg_parser = ArgumentParser()
    arg_parser.add_argument("input", help="Input File (JSON)")
    arg_parser.add_argument("-o", "--output", help="Output File (will be overwritten!)")
    arg_parser.add_argument("-f", "--format", choices=["kml", "json", "csv", "js", "gpx", "gpxtracks"], default="kml", help="Format of the output")
    arg_parser.add_argument("-v", "--variable", default="locationJsonData", help="Variable name to be used for js output")
    args = arg_parser.parse_args()
    if not args.output:  # if the output file is not specified, set to input filename with a diffrent extension
        args.output = '.'.join(args.input.split('.')[:-1]) + '.' + args.format
    if args.input == args.output:
        arg_parser.error("Input and output have to be different files")
        return

    p = loc_hist_parser()
    p.open_in_json(args.input)

    if args.format == "json" or args.format == "js":
        if args.format == "js":
            js_var = args.variable
        else:
            js_var = None

        p.export_to_json(args.output, js_var)

    if args.format == "csv":
        p.export_to_csv(args.output)

    if args.format == "kml":
        p.export_to_kml(args.output)

    if args.format == "gpx":
        p.export_to_gpx(args.output, False)

    if args.format == "gpxtracks":
        p.export_to_gpx(args.output, True)


# Haversine formula
def getDistanceFromLatLonInKm(lat1, lon1, lat2, lon2):
    R = 6371  # Radius of the earth in km
    dlat = deg2rad(lat2 - lat1)
    dlon = deg2rad(lon2 - lon1)
    a = math.sin(dlat / 2) * math.sin(dlat / 2) + \
        math.cos(deg2rad(lat1)) * math.cos(deg2rad(lat2)) * \
        math.sin(dlon / 2) * math.sin(dlon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = R * c  # Distance in km
    return d


def deg2rad(deg):
    return deg * (math.pi / 180)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
