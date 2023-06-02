from doc.quic_info import Quic_info
from doc.quic_info import Quic_info
from os.path import join as path_join
import json
import os
import shutil
import sys

def get_qlog_file(dir, type="client"):
    for file in os.listdir(dir):
        if file.split('.')[-1] == "qlog" and type in file:
            return os.path.join(dir, file)

def get_quic_info(file):
    if (file is None): return
    try:
        qi = Quic_info(file, "remote" if "server" in file else "local")
        output_file = file.rstrip(".qlog") + ".quic_info.json"
        with open(output_file, "w") as of:
            json.dump(qi.to_json(), of)
    except:
        print(f"Error while getting quic_info of {file}")

def apply_quic_info(workdir):
    json_template = path_join(workdir, 'output.json')
    graphs = []
    try:
        with open(json_template) as temp:
            graphs = json.load(temp)
    except FileNotFoundError:
        print("Can't get the directory")
        exit(-1)

    for method in graphs:
        for way in method['ways']:
            for param in way['params']:
                c_dir = path_join(workdir, method['method'], way['way'], str(param['param']))
                get_quic_info(get_qlog_file(c_dir, "client"))
                get_quic_info(get_qlog_file(c_dir, "server"))

if __name__ == "__main__":
    workdir = sys.argv[1]
    apply_quic_info(workdir)
