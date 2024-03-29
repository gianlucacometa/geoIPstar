####GIANLUCA COMETA - CISIA#####
import csv
import time
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
        except KeyError:  # If it fails, because there is no key
            super(DictList, self).__setitem__(key, value)
        except AttributeError:  # If it fails because it is not a list
            super(DictList, self).__setitem__(key, [self[key], value])


# lon/lat dictionary for some plot types
long_lat = dict()
long_lat2 = DictList()


def get_marker_color(size):
    if size < 1:
        return 'b'  # blue
    if size > 2 and size < 3:
        return 'g'  # green
    if size > 3 and size < 4:
        return 'c'
    if size > 4 and size < 5:
        return 'm'
    if size > 5:
        return 'r'  # red

def get_ip(ip_file):
    """
    Returns a list of IP addresses from a file containing one IP per line.
    """
    with contextlib.closing(ip_file):
        return [line.strip() for line in ip_file]

session = LimiterSession(per_minute=70)
def geo(ip_list=[], lats=[], lons=[]):
    file_name = 'test.csv'
    my_file = open(file_name, 'w', encoding='utf-8')
    writer = csv.writer(my_file)
    run_once_header = 0

    for ip in ip_list:
        try:
            time.sleep(0.40)
            loc = session.get('http://ip-api.com/json/%s?fields=24837887' % ip)
            print(ip)
            print(loc.headers)
            data = loc.json()
            if int(loc.headers['X-Rl']) == 1 or int(loc.headers['X-Rl']) == 0:
                time.sleep(10)
                print("X-Rl RAGGIUNTO - WAIT")

            #print(data.keys())
            if run_once_header == 0:
                my_file = open(file_name, 'w', encoding='utf-8')
                writer.writerow(data.keys())
                run_once_header = 1
            writer.writerow(data.values())
            my_file.close()
        except Exception:
            print("Unable to process IP: %s" % ip)
            continue
        if data is None:
            print("Unable to find info for IP: %s" % ip)
            continue
        lats.append(data['lat'])
        lons.append(data['lon'])

        # append to dictionary - to be used for later and where plot type needs it (it will only hold unique values)
        long_lat[ip] = {'lats': data['lat'], 'lons': data['lon']}
        # Experimental for heatmap
        long_lat2[ip] = {'lats': data['lat'], 'lons': data['lon']}
    return lats, lons


def generate_map(output, lats=[], lons=[], plottype=None, wesn=None, plotdest=None):
    """
    Using Basemap and the matplotlib toolkit, this function generates a map and
    puts a red dot at the location of every IP addresses found in the list.
    The map is then saved in the file specified in `output`. Depending on output
    type different picture is presented.
    """
    if (plottype == "connection" and plotdest == None):
        print(
            "[+] No destination specified. Please specify -d/--destination parameter with longitude and latitude as input (i.e. -d 53/12)")
        sys.exit(1)

    print("Generating map and saving it to {}".format(output))
    if wesn:
        wesn = [float(i) for i in wesn.split('/')]
        m = Basemap(projection='cyl', resolution='l',
                    llcrnrlon=wesn[0], llcrnrlat=wesn[2],
                    urcrnrlon=wesn[1], urcrnrlat=wesn[3])
    else:
        m = Basemap(projection='cyl', resolution='l')

    m.drawstates(linewidth=0.1, color="black")
    # plot type
    m.drawlsmask()
    # draw country map
    m.drawcountries(linewidth=0.1, color="black")
    # draw coastlines
    m.drawcoastlines(linewidth=0.1, color="black")

    # If plot type is scatter, draw markers as per https://matplotlib.org/3.2.2/api/_as_gen/matplotlib.pyplot.scatter.html
    if (plottype == "scatter"):
        x, y = m(lons, lats)
        m.scatter(x, y, s=1, color='#CA002A', marker='o', alpha=0.5)
        # save to file
        plt.savefig(output, dpi=1200, bbox_inches='tight')

    # If plot is bubble, draw normal plot with 'bubble-like' structures https://matplotlib.org/3.2.2/api/_as_gen/matplotlib.pyplot.plot.html#matplotlib.pyplot.plot
    if (plottype == "bubble"):
        for key, value in long_lat.items():
            m.plot(value['lons'], value['lats'], linestyle='none', marker="o", markersize=4, alpha=0.6, c="orange",
                   markeredgecolor="black", markeredgewidth=0.1)
        # save to file
        plt.savefig(output, dpi=1200, bbox_inches='tight')

    # If plot type is connectionmap, draw plot which joins connection source latitude and longitude (attacker IPs) with destination latitude and longitude
    if (plottype == "connectionmap" and plotdest != None):
        dst = [float(i) for i in plotdest.split('/')]
        # based on our dictionary with connections, draw the lines
        for key, value in long_lat.items():
            m.drawgreatcircle(value['lons'], value['lats'], dst[0], dst[1], linewidth=0.1, color='#CA002A')
        # save to file
        plt.savefig(output, dpi=1200, bbox_inches='tight')

    # If plot is heatmap, based it on number of occurances of certain IP
    if (plottype == "heatmap"):
        # Define base marker size
        min_marker_size = 0.5
        for keys in long_lat2:
            # grab only first lon-lat, the rest are repeated
            lonx = long_lat2[keys]
            laty = long_lat2[keys]
            marker_magnitude = (len(long_lat2[keys]) / 2) * min_marker_size
            # maintain some sort of control over marker size
            if (marker_magnitude > 5):
                marker_magnitude = 5
            marker_lonx = 0
            marker_laty = 0
            # if we got more than 2 elemetns in the list
            try:
                # grab first 2 elements, pass on unclear mapping
                if (len(lonx) > 2 and len(laty) > 2):
                    marker_lonx = list(lonx)[0]['lons']
                    marker_laty = list(laty)[0]['lats']
                else:
                    marker_lonx = lonx['lons']
                    marker_laty = lonx['lats']
                x, y = m(marker_lonx, marker_laty)
                msize = marker_magnitude * min_marker_size
                m.plot(x, y, 'ro', markersize=msize)
            except:
                pass

        # save to file
        plt.savefig(output, dpi=1200, bbox_inches='tight')

    if (plottype == "hexbin"):
        x, y = m(lons, lats)
        m.hexbin(array(x), array(y), gridsize=40, mincnt=1, cmap='jet', norm=colors.LogNorm(), linewidths=0.1)
        plt.savefig(output, dpi=1200, bbox_inches='tight')


def main():
    arguments = argparse.ArgumentParser(description='Visualize IP addresses on the map')
    arguments.add_argument('-i', '--input', dest="input", type=argparse.FileType('r'),
                           help='Input file. One IP per line', default=sys.stdin)
    arguments.add_argument('-o', '--output', default='output.png', help='Path to save the file (e.g. /tmp/output.png)')
    arguments.add_argument('-e', '--extents', default=None,
                           help='Extents for the plot (west/east/south/north). Default to globe.')
    arguments.add_argument("-t", "--type", default="scatter",
                           help="Plot type scatter, bubble, connectionmap, heatmap, hexbin")
    arguments.add_argument("-d", "--destination", default=None,
                           help="When connectionmap line plot is used, add latitude and longitude as destination (i.e. -d 51.50/0.12)")
    args = arguments.parse_args()

    # Get output to file
    output = args.output

    ip_list = get_ip(args.input)
    lats, lons = geo(ip_list)

    # Call final function to start drawing on the map
    generate_map(output, lats, lons, plottype=args.type, wesn=args.extents, plotdest=args.destination)


if __name__ == '__main__':
    main()
