import cbor2 # pip3 install cbor2
from os.path import join as path_join
import json
import os
import shutil
import sys

# Compress qlog with CBOR
# Compress all the files

def remove_pcap(dir):
    for file in os.listdir(dir):
        if file.split('.')[-1] == "pcap":
            os.remove(os.path.join(dir, file))

def get_qlog_file(dir, type="client"):
    for file in os.listdir(dir):
        if file.split('.')[-1] == "qlog" and type in file:
            return os.path.join(dir, file)

def compress(input_file):
    if (input_file == None): return
    with open(input_file) as file:
        compressed = cbor2.dumps(file.read())

    with open(f"{input_file}.cbor", "wb") as file:
        file.write(compressed)

    os.remove(input_file)

def main_compress(workdir):
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
                c_dir = path_join(
                    workdir, method['method'], way['way'], str(param['param']))
                compress(get_qlog_file(c_dir, "client"))
                compress(get_qlog_file(c_dir, "server"))
                remove_pcap(c_dir)

    shutil.make_archive(workdir, 'zip', workdir)
    shutil.rmtree(workdir, ignore_errors=True)

if __name__ == "__main__":
    workdir = sys.argv[1]
    main_compress(workdir)
