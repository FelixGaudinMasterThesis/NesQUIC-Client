import requests
import json
from geopy.distance import distance
# https://github.com/pydata/numexpr/blob/master/numexpr/cpuinfo.py
import client.cpuinfo
import netifaces
import socket
import subprocess

def loc_to_coord(loc):
    t = loc.split(',')
    return float(t[0]), float(t[1])

def get_buffer_size():
    cmd = "sysctl -a 2>/dev/null | grep rmem_max | grep -Eo '[0-9]+$'"
    return int(subprocess.check_output(cmd, shell=True))
    
def get_meta_data(host):
    server_ip = socket.gethostbyname(host)
    data = {}
    # IP INFO
    # https://github.com/librespeed/speedtest/blob/node/src/SpeedTest.js#L56
    client_res = requests.get("https://ipinfo.io/json")
    if client_res.status_code == 200:
        tmp = json.loads(client_res.content)
        del tmp['readme']
        tmp['loc'] = loc_to_coord(tmp['loc'])
        data.update(tmp)
        # get server coordinates
        server_res = requests.get(f"https://ipinfo.io/{server_ip}/json")
        if server_res.status_code == 200:
            tmp = json.loads(server_res.content)
            server_coord = loc_to_coord(tmp['loc'])
            data['distance'] = distance(data['loc'], server_coord).km
    # CPU info
    # https://stackoverflow.com/questions/4842448/getting-processor-information-in-python
    data["CPU"] = client.cpuinfo.cpu.info[0]['model name']
    # Network interfaces
    # https://stackoverflow.com/questions/270745/how-do-i-determine-all-of-my-ip-addresses-when-i-have-multiple-nics
    inters = {}
    for interface in netifaces.interfaces():
        for link in netifaces.ifaddresses(interface)[netifaces.AF_INET]:
            inters[interface] = link['addr']
    data['Network_interfaces'] = inters
    # rmem_max
    data["rmem_max"] = get_buffer_size()
    
    return data
