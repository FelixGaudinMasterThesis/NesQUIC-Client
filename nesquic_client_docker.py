import os
from client.nesquic_client_aux import start_client

def launch_client(test_name, destination, port):
    base_dir = "."
    session_dir = os.path.join(base_dir, 'logs', test_name)

    start_client(
        destination=destination,
        port=port,
        nesquic_path="nesquic",
        test_duration=20,
        size=50_000_000,
        bw_probe_cc="bbr",
        test_interval_duration=2,
        session_dir=session_dir,
        verbose=True,
        methods=["bulk", "limited"],
        dump=False,
        compress=False
    )
