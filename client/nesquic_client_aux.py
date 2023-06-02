from client.nesquic_utils import NesQuic
import logging
import time
from datetime import timedelta
import os
import json
from client.meta_data import get_meta_data
from time import sleep

def start_client(
        destination: str, 
        port: int, 
        nesquic_path :str, 
        test_duration: int, 
        size: int, 
        bw_probe_cc: str, 
        test_interval_duration: int, 
        session_dir: str, 
        verbose: bool, 
        methods: list, 
        dump: bool, 
        client_port = None,
        compress = False
    ):
    nesquic = NesQuic(
        destination, 
        port, 
        nesquic_path,
        test_duration, 
        size, 
        bw_probe_cc, 
        test_interval_duration, 
        dump, 
        client_port,
        compress
    )

    # Verbosing
    tqdm = lambda x : x 
    if verbose:
        from tqdm import tqdm
        logging.basicConfig(level=logging.INFO)

    out_structure = []

    methods_params = {
        'limited' : {
            'ways': ['download', 'upload'],
            'params': [0.3, 0.5, 0.8, 0.9, 1.0, 1.1],
            'param_name': 'step',
            'function' : nesquic.limited_test
        },
        'bulk' : {
            'ways': ['download', 'upload'],
            'params': ['reno', 'bbr', 'cubic', 'fast'],
            'param_name': 'cc_algs',
            'function' : nesquic.bulk_test
        }
    }

    start_time = time.time()
    for method in methods:
        current_structure = {
            "method": method,
            "ways": [],
            "param_title": methods_params[method]['param_name']
        }
        for way in methods_params[method]["ways"]:
            logging.info(f"Running {method} tests on {way}")
            data = {
                "way": way,
                'params': []
            }
            for param in tqdm(methods_params[method]['params']):
                c_dir = os.path.join(session_dir, method, way)
                timestamp = int(time.time())
                out = methods_params[method]['function'](c_dir, way, param)
                if out != None:
                    param_format, output_info = out
                    data['params'].append({
                        'param': param_format,
                        'infos' : output_info,
                        'timestamp' : timestamp
                    })
                sleep(10) # Timeout to avoid error reusing socket
            current_structure['ways'].append(data)
        out_structure.append(current_structure)

    with open(os.path.join(session_dir, 'output.json'), 'w') as file:
        json.dump(out_structure, file)

    meta_data = get_meta_data(destination)
    meta_data['client_port'] = nesquic.client_port
    meta_data['server_port'] = nesquic.port
    with open(os.path.join(session_dir, 'meta_data.json'), 'w') as file:
        json.dump(meta_data, file)

    logging.info("Elapsed time : %s", str(
        timedelta(seconds=time.time() - start_time)))
