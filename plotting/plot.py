import matplotlib.pyplot as plt
import json
from tqdm import tqdm
from utils import get_save_dir
from templates import templates

import argparse
from os.path import join as path_join

templates

# Parser
parser = argparse.ArgumentParser(
    description='NesQuic client graph maker')
parser.add_argument('workdir', type=str, help='Directory')
parser.add_argument('plot_type', type=str,
                    help=f'Tests list : {", ".join(templates.keys())}')
parser.add_argument('-v', '--verbose', action='store_true', dest='verbose',
                    help='Printing evolution')

args = parser.parse_args()
# Get args
plot_type = args.plot_type
if not plot_type in templates:
    print(f'Unknown plot type "{plot_type}"')
    exit(-1)
workdir = args.workdir
tqdm = tqdm if args.verbose else lambda x:x
# Gettings template file
json_template = path_join(workdir, 'output.json')
graphs = []
try:
    with open(json_template) as temp:
        graphs = json.load(temp)
except FileNotFoundError:
    print("Can't get the directory")
    exit(-1)

save_dir = get_save_dir(workdir)

for method in graphs:
    for way in method['ways']:
        test_title = f"{method['method']}_{way['way']}_{plot_type}"
        if args.verbose: print(f"Loading {test_title}")
        data = []
        for param in tqdm(way['params']):
            c_dir = path_join(workdir, method['method'], way['way'], str(param['param']))
            data.append(
                templates[plot_type]['get_data'](
                    c_dir,
                    param,
                    way = way["way"])
            )
        templates[plot_type]['plot_data'](
            title=test_title,
            legend_title=method['param_title'], 
            data=data, template=templates[plot_type], save_dir=save_dir)
        # plt.show())
