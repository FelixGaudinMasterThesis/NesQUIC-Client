from datetime import datetime
import argparse, os
from client.nesquic_client_aux import start_client
import shutil

# Instantiate the parser
parser = argparse.ArgumentParser(
    description='NesQuic client utility (by default it take in average 7min)')

parser.add_argument('name', type=str, help='Name of the test')
parser.add_argument('destination', type=str, help='Server')
parser.add_argument('port', type=int, help='Server PORT')


parser.add_argument('-e', '--nesquic', type=str, dest="nesquic_path",
                    help='Max duration of the test', default="nesquic")
parser.add_argument('-d', '--duration', type=int, dest="duration",
                    help='Max duration of the test', default=20)
parser.add_argument('-i', '--interval', type=int, dest="interval",
                    help='Test interval duration', default=2)
parser.add_argument('-c', '--cc_alg', type=str, dest="cc_alg",
                    help='Congestion algorithm use to test bw', default="bbr")
parser.add_argument('-s', '--size', type=int, dest="size",
                    help='Size of tests', default=50_000_000)
parser.add_argument('-o', '--ouput-dir', type=str, dest="base_dir",
                    help='Output directory', default='./')

parser.add_argument('-b', '--bulk', action='store_true', dest='bulk',
                    help='If doing bulk test')
parser.add_argument('-l', '--limited', action='store_true', dest='limited',
                    help='If doing limited test')
parser.add_argument('-v', '--verbose', action='store_true', dest='verbose',
                    help='Printing logs')
parser.add_argument('-D', '--dump', action='store_true', dest='dump',
                    help='Store tcp dump pcap')
parser.add_argument('-C', '--compress', action='store_true', dest='compress',
                    help='Compress qlogs')
parser.add_argument('-Z', '--zip', action='store_true', dest='zip',
                    help='Compress qlogs and compress all results in a zip file')

args = parser.parse_args()

# Avoid empty test
if (not args.bulk) and (not args.limited):
    print("No test to do")
    print("Use -b (--bulk) or -l (--limited) to perform tests")
    exit(-1)

# Very basic input checking
if (args.duration <= 0 or args.interval <= 0 or (not args.cc_alg in ['reno', 'bbr', 'cubic']) or args.size <= 0):
    exit(-1)

# Set session dir
base_dir = args.base_dir
test_name = args.name
session_dir = os.path.join(base_dir, 'logs', test_name, datetime.now().ctime().replace("  ", " ").replace(" ", "_"))

# Get used methods
methods = []
if args.bulk:
    methods.append('bulk')
if args.limited:
    methods.append('limited')

# Optimize compression with compressing qlogs
if args.zip:
    args.compress = True

start_client(
    destination            = args.destination,
    port                   = args.port,
    nesquic_path           = args.nesquic_path,
    test_duration          = args.duration,
    size                   = args.size,
    bw_probe_cc            = args.cc_alg,
    test_interval_duration = args.interval,
    session_dir            = session_dir,
    verbose                = args.verbose,
    methods                = methods,
    dump                   = args.dump,
    compress               = args.compress
)

if (args.zip) :
    shutil.make_archive(session_dir, 'zip', session_dir)
    shutil.rmtree(session_dir, ignore_errors=True)
