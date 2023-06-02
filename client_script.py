import subprocess
import os
import requests
import json
from nesquic_client_docker import launch_client
from compress import main_compress as compress
from apply_quic_info import apply_quic_info
import shutil
from werkzeug.utils import secure_filename

TEST_NAME = "unknown"
HOSTNAME = os.environ["HOSTNAME"]
HOST_PORT = os.environ["HOST_PORT"]


if __name__ == "__main__":
    print("Welcome to NesQUIC")
    print("This tool will do several tests on your connexion")
    print("The data exchanged can be high (about 3Go) so we would not recommand you to do this on a telephone subscription")
    print()
    print("To get results of the test, you can add the '--volume your/path:/output' option in docker run")
    print()
    reply = input("Are you sure you want to do the tests ? (y/n)")
    if (reply == "y" or reply == "Y"):
        print()
        rmem_max = int(subprocess.check_output(['cat', '/proc/sys/net/core/rmem_max']))
        if (rmem_max >= 2500000):
            print("Buffer size ok")
            print()
            reply = input("Can you put your name/info about your connexion :\n")
            TEST_NAME = secure_filename(reply)
            if TEST_NAME == "": TEST_NAME = "unknown"
            # get id
            res = requests.get(
                f'http://{HOSTNAME}:5000/get-id',
                # note : https://requests.kennethreitz.org/en/latest/user/advanced/#timeouts
                timeout=(30, None))

            if (res.status_code == 401):
                print("Another test is running on the server. Please retry in 5-10min.")
                exit(0)
            elif (res.status_code == 200):
                id = json.loads(res.content).get('id')
                if (id is None):
                    print("Error while getting test id")
                    exit(1)
                
                print("Test id ok")
                print("Starting NesQUIC tests (+- 10min)")

                launch_client(
                    test_name=TEST_NAME,
                    destination=HOSTNAME,
                    port=HOST_PORT
                )

                print("Test finished")
                print()
                print("Sending logs to server")

                shutil.copytree(
                    os.path.join("logs", TEST_NAME),
                    TEST_NAME
                )

                compress(TEST_NAME)

                res = requests.post(
                    f'http://{HOSTNAME}:5000/upload/{id}',
                    files={'file': open(f"{TEST_NAME}.zip", 'rb')}
                )

                if res.status_code == 200:
                    print("Successfully send data to server !")
                else:
                    print(res)

                os.remove(f"{TEST_NAME}.zip")

                print("Sending finished")
                print()

                shutil.move(
                    os.path.join("logs", TEST_NAME),
                    "/output/"
                )

                print("Do you want to plot graphs about your connexion ?")
                reply = input("They will be store in the output folder (y/n)")
                if (reply == "y" or reply == "Y"):
                    print("Plotting results")
                    print()
                    subprocess.check_call([
                        "bash",
                        "/usr/src/app/all_plots.bash",
                        os.path.join("/output", TEST_NAME)
                    ])
                
                print("Do you want quic_info of each connexion ? (a tcp_info like for quic)")
                reply = input("They will be store in the output folder (y/n)")
                if (reply == "y" or reply == "Y"):
                    apply_quic_info(os.path.join("/output", TEST_NAME))
                
                print("Thank you a lot for your contribution !")
                print(f"Your test id is {id}")

        else:
            print(f"Your buffer size is {rmem_max}, please increase it to 2.500.000")
            print("To do this, you can follow the instruction described here :")
            print("https://github.com/quic-go/quic-go/wiki/UDP-Receive-Buffer-Size")
