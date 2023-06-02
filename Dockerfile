FROM ubuntu:22.04

# Nesquic build

RUN apt-get update && \
    apt-get install -y build-essential git cmake software-properties-common \
    openssl libssl-dev pkg-config clang python3-pip tcpdump zip


RUN mkdir /nesquic
COPY nesquic /nesquic/

WORKDIR /nesquic/deps/picotls
RUN rm -rf CMakeCache.txt CMakeFiles && cmake . && make -j 8

WORKDIR /nesquic/deps/picoquic
RUN rm -rf CMakeCache.txt CMakeFiles && cmake . && make -j 8

WORKDIR /nesquic
RUN rm -rf CMakeCache.txt CMakeFiles && cmake . && make -j 8
RUN cp ./nesquic /bin/nesquic

#################
# Nesquic tools #
#################

WORKDIR /usr/src/app

RUN pip3 install cbor2 requests geopy netifaces tqdm matplotlib pandas werkzeug

# Client
COPY client client
COPY nesquic_client_docker.py .
# Sending to server
COPY compress.py .
# COPY send_file.py .
# Quic info
COPY doc/quic_info.py doc/quic_info.py
COPY apply_quic_info.py .
# Plotting
COPY nesquic_tests/plotting plotting

COPY nesquic_tests/all_plots.bash .
# Main script
COPY client_script.py .
# Output folder
RUN mkdir /output

##########################
# Environement variables #
##########################
ENV HOSTNAME=speedtest.rysingan.dev
ENV HOST_PORT=4443

CMD [ "python3", "client_script.py" ]