import argparse
import contextlib
import json
import sys
from requests import Session
from requests_ratelimiter import LimiterSession

from requests import get
session = LimiterSession(per_minute=1)

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