import cbor2 # pip3 install cbor2
import subprocess
import os
import logging
import tempfile
import json
import time
import requests

def get_first_qlog_file(dir):
    for file in os.listdir(dir):
        if file.split('.')[-1] == "qlog" and "client" in file:
            return os.path.join(dir, file)

def compress_qlog(input_file):
    if (input_file == None): return
    with open(input_file) as file:
        compressed = cbor2.dumps(file.read())

    with open(f"{input_file}.cbor", "wb") as file:
        file.write(compressed)

    os.remove(input_file)

def run(*args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, 
        shell=False, env=None, timeout=None, background=False):
    kwargs = {}
    if env:
        kwargs['env'] = os.environ.copy()
        kwargs['env'].update(env)
    p = subprocess.Popen(*args, universal_newlines=True,
                         shell=shell, stdout=stdout, stderr=stderr, **kwargs)
    try:
        if background:
            return p
        code = p.wait(timeout=timeout)
        if code != 0 or stdout is subprocess.DEVNULL:
            return code
        try:
            return p.stdout.read()
        except:
            return code
    except:
        p.terminate()
        return 'timeout'

def find_port():
    import socket
    sock = socket.socket()
    sock.bind(('', 0))
    port = sock.getsockname()[1]
    sock.close()
    return port

class NesQuic:

    def __init__(
            self, 
            destination: str, 
            port: int, 
            nesquic_path: str,
            test_duration: int = 20, 
            size: int = 50_000_000, 
            bw_probe_cc: str = "bbr",
            test_interval_duration: int = 2, 
            store_dump : bool = False, 
            client_port = None,
            compress : bool = False
        ):
        self.destination = destination
        self.port = port
        self.nesquic_path = nesquic_path
        self.client_port = find_port() if client_port == None else client_port
        self.estimated_bw = {}
        self.test_duration = test_duration
        self.test_interval_duration = test_interval_duration
        self.size = size
        self.bw_probe_cc = bw_probe_cc
        self.store_dump = store_dump
        self.compress = compress

    def __str__(self) -> str:
        return f"""
        NesQuic Client ({hex(id(self))})
        destination : {self.destination}
        port : {self.port}   
        nesquic_path : {self.nesquic_path}   
        client_port : {self.client_port}
        estimated_bw : {self.estimated_bw}   
        test_duration : {self.test_duration}  
        test_interval_duration : {self.test_interval_duration} 
        size : {self.size}   
        bw_probe_cc : {self.bw_probe_cc}
        store_dump : {self.store_dump} 
        """

    def nesquic(self, env={}, **test_args):
        with tempfile.NamedTemporaryFile() as f:
            env['NESQUIC_STATS_FILENAME'] = f.name
            code = run([self.nesquic_path, '-c',
                        "-H", self.destination, "-P",  str(self.port), 
                        "-p", str(self.client_port), json.dumps(test_args)], 
                        env=env)
            if code != 0:
                logging.warning("Test failed with return code %d", code)
                return
            with open(f.name) as f:
                test_output = json.load(f)
                return test_output


    def get_bw(self, way: str, size: int, 
                        cc: str, max_duration_s: int, interval_duration_s: int):
        test_output = self.nesquic( 
                     testname='bulk', way=way, size=size, cc_alg=cc, 
                     max_duration_s=max_duration_s,
                     interval_duration_s=interval_duration_s)
        if test_output is None:
            return -1
        total_data_exchanged = test_output[-1]['stream_data_received'] if way == 'download' else test_output[-1]['stream_data_sent']
        total_elapsed_s = test_output[-1]['elapsed_s']
        if len(test_output) < 3:
            data_exchanged = total_data_exchanged
            elapsed_s = total_elapsed_s
        else:
            stream_data_received = test_output[-1]['stream_data_received'] - \
                test_output[1]['stream_data_received']
            stream_data_sent = test_output[-1]['stream_data_sent'] - \
                test_output[1]['stream_data_sent']
            data_exchanged = stream_data_received if way == 'download' else stream_data_sent
            elapsed_s = test_output[-1]['elapsed_s'] - \
                test_output[1]["elapsed_s"]
        if elapsed_s == 0:
            logging.warn("Can't get BW")
            return -1, 0
        return data_exchanged / elapsed_s * 8, elapsed_s

    def get_server_qlogs(self, session_dir):
        # try to get qlogs serveur side
        client_qlogs = None
        n_try = 0
        while client_qlogs == None:
            client_qlogs = get_first_qlog_file(session_dir)
            time.sleep(1)
            if n_try > 30: break
            n_try += 1
        if client_qlogs == None:
            logging.warn("Couldn't get qlogs")
            return
        server_qlogs = client_qlogs.replace("client", "server")
        status_code = 418
        n_try = 0
        while status_code != 200:
            res = requests.get(
                f'http://{self.destination}:5000/download/{server_qlogs.split("/")[-1]}',
                # note : https://requests.kennethreitz.org/en/latest/user/advanced/#timeouts
                timeout=(10, None))
            status_code = res.status_code
            time.sleep(1)
            if n_try > 30: break
            n_try += 1
        if status_code == 200:
            with open(server_qlogs, 'wb') as file:
                file.write(res.content)
            if self.compress:
                compress_qlog(server_qlogs)
        else:
            logging.warn("Couldn't get server qlogs")
            print(f"Status code : {status_code}")
            print(res.content)

        if self.compress:
            compress_qlog(client_qlogs)

    def test(self, session_dir: str, way, **test_args):
        os.makedirs(session_dir)
        os.environ['NESQUIC_CLIENT_QLOG_DIR'] = session_dir
        os.environ['NESQUIC_CLIENT_PERF_FILE'] = str(os.path.join(session_dir, "client_perflog.csv"))
        env = {}
        if self.store_dump:
            env = {'SSLKEYLOGFILE' : os.path.join(session_dir, 'secrets.txt')}

            tcpdump = run([
                    'tcpdump', '-i', 'any',
                    f'udp port {self.port}',
                    '-w', os.path.join(session_dir, 'client.pcap')
                ], background=True, stderr=subprocess.PIPE)
            time.sleep(0.5)
            ret = tcpdump.poll()
            if ret:
                print("tcpdump terminated:")
                out, err = tcpdump.communicate()
                print(err)
                exit()
        
        test_output = self.nesquic(way=way, env=env, **test_args)

        self.get_server_qlogs(session_dir)

        if self.store_dump: tcpdump.terminate()

        if test_output is None: return -1, -1

        total_data_exchanged = test_output[-1]['stream_data_received'] if way == 'download' else test_output[-1]['stream_data_sent']
        total_elapsed_s = test_output[-1]['elapsed_s']
        return total_data_exchanged, total_elapsed_s


    def limited_test(self, session_dir, way, step):
        if not way in self.estimated_bw:
            if 'NESQUIC_CLIENT_QLOG_DIR' in os.environ: del os.environ['NESQUIC_CLIENT_QLOG_DIR']
            bw_tests = [self.get_bw(way, self.size * 4, cc=self.bw_probe_cc,
                                    max_duration_s=self.test_duration,
                                    interval_duration_s=self.test_interval_duration) 
                                    for _ in range(3)]
            bw, _ = max(bw_tests)
            self.estimated_bw[way] = bw
        if self.estimated_bw[way] == -1:
            logging.warn(f"Can't get bw for limited {way}")
            return None
        bps = self.estimated_bw[way] * step
        output_dir = f"{step} ({bps/1000_000:.2f} Mbps)"
        data_exchanged, elapsed_s = self.test(
                     os.path.join(session_dir, output_dir), 
                     testname='limited_transfer', way=way,
                     size=self.size * 100, bps=bps, 
                     max_duration_s=self.test_duration)
        output_info = {
            'limited_bps' : bps,
            'data_exchanged' : data_exchanged,
            'elapsed_s': elapsed_s
        }
        return output_dir, output_info

    def bulk_test(self, session_dir, way, cc):
        # logging.info("Performing %s bulk test with cc=%f", way, cc)
        data_exchanged, elapsed_s = self.test(
                session_dir=os.path.join(session_dir, cc), 
                testname='bulk', way=way,
                size=self.size, cc_alg=cc, max_duration_s=self.test_duration)
        output_info = {
            'cc_alg' : cc,
            'data_exchanged' : data_exchanged,
            'elapsed_s': elapsed_s
        }
        return cc, output_info
