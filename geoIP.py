####GIANLUCA COMETA - CISIA#####
import argparse
import contextlib
import json
import sys
from requests import Session
from requests_ratelimiter import LimiterSession

###FROM GEOIPPlotter###
# Imports
import argparse
import contextlib
import sys
import matplotlib
import numpy as np
# Anti-Grain Geometry (AGG) backend so PyGeoIpMap can be used 'headless'
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from matplotlib import cm
from numpy import array
import matplotlib.colors as colors

# Adopted from https://stackoverflow.com/questions/10664856/make-a-dictionary-with-duplicate-keys-in-python
# This class will allow us to store multiple iterations of the samle lat/lon for specific IP so we can establish weight
class DictList(dict):
    def __setitem__(self, key, value):
        try:
            # Assumes there is a list on the key
            self[key].append(value)
        except KeyError: # If it fails, because there is no key
            super(DictList, self).__setitem__(key, value)
        except AttributeError: # If it fails because it is not a list
            super(DictList, self).__setitem__(key, [self[key], value])


#lon/lat dictionary for some plot types
long_lat = dict()
long_lat2=DictList()

def get_marker_color(size):
    if size < 1:
        return 'b'#blue
    if size > 2 and size < 3:
        return 'g' # green
    if size > 3 and size < 4:
        return 'c'
    if size > 4 and size < 5:
        return 'm'
    if size > 5:
        return 'r' #red



from requests import get
session = LimiterSession(per_second=10)

def get_ip(ip_file):
    """
    Returns a list of IP addresses from a file containing one IP per line.
    """
    with contextlib.closing(ip_file):
        return [line.strip() for line in ip_file]


def geo(ip_list=[]):
    for ip in ip_list:
        try:
            loc = session.get('http://ip-api.com/json/%s?fields=24837887' % ip)
            print(ip)
            data = loc.json()
            print(data)
            print(data['country'])
            print(data['lat'])
            print(data['lon'])
        except Exception:
            print("Unable to process IP: %s" % ip)
            continue




def main():
    arguments = argparse.ArgumentParser(description='Visualize IP addresses on the map')
    arguments.add_argument('-i', '--input', dest="input", type=argparse.FileType('r'), help='Input file. One IP per line', default=sys.stdin)
    args = arguments.parse_args()
    ip_list = get_ip(args.input)
    geo(ip_list)
if __name__ == '__main__':
    main()