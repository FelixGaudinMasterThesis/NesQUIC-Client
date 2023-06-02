import os
import numpy as np
import json
import pandas as pd
from matplotlib import ticker
import matplotlib.pyplot as plt

def get_events(qlogs):
    return qlogs['traces'][0]['events']

def get_rtts(qlogs):
    timestamps = []
    rtts = []
    for event in get_events(qlogs):
        if "latest_rtt" in event[3]:
            timestamps.append(event[0]/1000)
            rtts.append(event[3]["latest_rtt"]/1000)
    return timestamps, rtts

def get_smoothed_rtts(qlogs):
    timestamps = []
    rtts = []
    for event in get_events(qlogs):
        if "smoothed_rtt" in event[3]:
            timestamps.append(event[0]/1000)
            rtts.append(event[3]["smoothed_rtt"]/1000)
    return timestamps, rtts

def get_losses(qlogs):
    timestamps, pkt_numbers = [], []
    for event in get_events(qlogs):
        if "packet_lost" == event[2]:
            timestamps.append(event[0]/1000)
            pkt_numbers.append(event[3]['packet_number'])
    return timestamps, pkt_numbers

def get_cwnd(qlogs):
    timestamps, cwnd = [], []
    for event in get_events(qlogs):
        if "metrics_updated" == event[2] and 'cwnd' in event[3]:
            timestamps.append(event[0]/1000)
            cwnd.append(event[3]['cwnd'])
    return timestamps, cwnd


def get_qlog_file(dir, type="client"):
    for file in os.listdir(dir):
        if file.split('.')[-1] == "qlog" and type in file:
            return os.path.join(dir, file)


def get_client_qlog_file(dir):
    return get_qlog_file(dir, "client")

def get_server_qlog_file(dir):
    return get_qlog_file(dir, "server")

def get_save_dir(workdir):
    save_dir = os.path.join(workdir, 'graphs')
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    return save_dir

# not in template file !!!
def plot_cdf(ax, data, label):
    count, bins_count = np.histogram(data, bins=len(data))
    pdf = count / sum(count)
    cdf = np.cumsum(pdf)
    ax.plot(bins_count[1:], cdf, label=label)
    


def get_info_rtts_cdf(dir, param, way=None):
    file = get_client_qlog_file(dir)
    if file == None: return
    with open(file) as file:
        _, rtts = get_rtts(json.load(file))
        return {
            'rtts' : rtts,
            'label' : param['param']
        }

def plot_rtts_cdf(title, legend_title, data, template, save_dir):
    fig, ax = plt.subplots(figsize=template.get('figsize', None))
    for param_data in data:
        if param_data != None:
            plot_cdf(ax, param_data['rtts'], str(param_data['label']))
    fig.suptitle(title)
    fig.legend(title=legend_title)
    ax.set_xlabel(template['xlabel'])
    ax.set_ylabel(template['ylabel'])
    fig.savefig(os.path.join(save_dir, f'{title}.pdf'))

def get_info_rtts_evolution(dir, param, way=None):
    file = get_client_qlog_file(dir)
    if file == None: return
    with open(file) as file:
        timestamps, rtts = get_rtts(json.load(file))
        return {
            'rtts' : rtts,
            'timestamps' : timestamps,
            'label' : param['param']
        }

def plot_rtts_evolution(title, legend_title, data, template, save_dir):
    fig, ax = plt.subplots(figsize=template.get('figsize', None))
    for param_data in data:
        if param_data != None:
            ax.plot(
                [t/1000 for t in param_data['timestamps']],
                param_data['rtts'], label=param_data['label']
                )
    fig.suptitle(title)
    fig.legend(title=legend_title)
    ax.set_xlabel(template['xlabel'])
    ax.set_ylabel(template['ylabel'])
    fig.savefig(os.path.join(save_dir, f'{title}.pdf'))

def get_info_smoothed_rtts_evolution(dir, param, way=None):
    file = get_client_qlog_file(dir)
    if file == None: return
    with open(file) as file:
        timestamps, rtts = get_smoothed_rtts(json.load(file))
        return {
            'rtts': rtts,
            'timestamps': timestamps,
            'label': param['param']
        }

def get_info_comp_table(dir, param, way=None):
    file = get_client_qlog_file(dir)
    if file == None: return
    with open(file) as file:
        data = json.load(file)
        _, rtts = get_rtts(data)
        to_return = {
            'label' : param['param'],
            'data exchanged (B)' : param['infos']['data_exchanged'],
            'elapsed time (s)': param['infos']['elapsed_s'],
            'estimated bw (Mbps)': 8*param['infos']['data_exchanged']/(param['infos']['elapsed_s']*1000_000),
            'min rtts (ms)' : np.min(rtts),
            'mean rtts (ms)' : np.mean(rtts),
            'median rtts (ms)' : np.median(rtts),
            '0.8 quantil (ms)': np.quantile(rtts, 0.8),
            '0.9 quantil (ms)': np.quantile(rtts, 0.9),
            '0.99 quantil (ms)': np.quantile(rtts, 0.99),
        }
        return {
            k:(f"{v:,.2f}" if isinstance(v, (float, int)) else v) for k, v in to_return.items()
        }

def plot_comp_table(title, legend_title, data, template, save_dir):
    fig, ax = plt.subplots(figsize=template.get('figsize', None))

    fig.patch.set_visible(False)
    ax.axis('off')
    ax.axis('tight')

    df = pd.DataFrame(data)
    df.rename(columns={"label":legend_title})

    table = ax.table(cellText=df.values, colLabels=df.columns, loc='center')
    table.auto_set_font_size(False)
    table.scale(1.2, 1.2)
    table.auto_set_column_width(col=list(range(len(df.columns))))
    fig.suptitle(title)
    fig.savefig(os.path.join(save_dir, f'{title}.pdf'))

def get_info_complet(dir, param, way=None):
    file = get_client_qlog_file(dir)
    if file == None: return
    with open(file) as file:
        qlogs = json.load(file)
        # Losses processing
        lt, ln = get_losses(qlogs)
        delta_times = []
        counts = []
        if len(ln) > 0:
            curr_start_ts = lt[0]
            curr_count = 1
            for i in range(1, len(ln)):
                delta = ln[i] - ln[i-1]
                if delta > 10:
                    delta_times.append(
                        (curr_start_ts, lt[i-1]),
                    )
                    counts.append(curr_count)
                    curr_count = 1
                    curr_start_ts = lt[i]
                else:
                    curr_count += 1
            delta_times.append(
                (curr_start_ts, lt[-1]),
            )
            counts.append(curr_count)
        # Rtts / cwin
        t, r = get_rtts(qlogs)
        st, sr = get_smoothed_rtts(qlogs)
        tt = c = None
        if way == "upload":
            tt, c = get_cwnd(qlogs)
        return {
            "param" : param["param"],
            "losses_delta_times" : delta_times,
            "losses_counts" : counts,
            "rtts_timestamps" : t,
            "rtts_values" : r,
            "smoothed_rtts_timestamps" : st,
            "smoothed_rtts_values" : sr,
            "cwnd_timestamps" : tt,
            "cwnd_values" : c
        }


def plot_complet(title, legend_title, data, template, save_dir):

    can_use_cwnd = data[0]["cwnd_values"] != None
    fig, axs = plt.subplots(
        nrows=4 if can_use_cwnd else 3,
        sharex=True,
        subplot_kw=dict(frameon=False),
        figsize=(17, 15)
        # figsize=(10, 20) if can_use_cwnd else (10, 15)
    )
    cmap = plt.get_cmap("tab10")
    for i, param in enumerate(data):
        color = cmap(i)

        axs[0].grid()
        axs[0].plot(param["rtts_timestamps"], param["rtts_values"], label=str(param['param']), color=color)
        axs[0].set_ylabel('RTTS (ms)')
        axs[0].tick_params('x')
        axs[0].xaxis.set_tick_params(which='both', labelbottom=True)

        axs[1].grid()
        axs[1].plot(param["smoothed_rtts_timestamps"],
                    param["smoothed_rtts_values"], color=color)
        axs[1].set_ylabel('Smoothed RTTS (ms)')
        axs[1].xaxis.set_tick_params(which='both', labelbottom=True)

        axs[2].grid()
        for dt, count in zip(param["losses_delta_times"], param["losses_counts"]):
            axs[2].fill_between(dt, [count, count], color=color, alpha=0.5)
        # axs[2].hist(param["losses"], range=[
        #             0, param["rtts_timestamps"][-1]], bins=100, alpha=0.5)
        axs[2].set_ylabel('Losses burst size')
        # axs[2].xaxis.set_tick_params(which='both', labelbottom=True)

        if can_use_cwnd:
            axs[3].grid()
            axs[3].set_ylabel('CWND size')
            axs[3].plot(param["cwnd_timestamps"], param["cwnd_values"], color=color)
            axs[3].yaxis.set_major_formatter(
                ticker.FuncFormatter(lambda y, pos: f"{int(y//1000)}K"))
            axs[3].set_xlabel('Timestamps (ms)')
        else:
            axs[2].set_xlabel('Timestamps (ms)')

    fig.suptitle(title)
    fig.legend(title=legend_title)
    fig.savefig(os.path.join(save_dir, f'{title}.pdf'))


def get_info_one_way_rtt(dir, param, way=None):
    client_qlogs, server_qlogs = None, None

    client_qlog_file = get_client_qlog_file(dir)
    server_qlog_file = get_server_qlog_file(dir)
    try :
        with open(client_qlog_file) as cf:
            client_qlogs = json.load(cf)

        with open(server_qlog_file) as sf:
            server_qlogs = json.load(sf)

        sdr_qlogs = server_qlogs if way == "download" else client_qlogs
        rcv_qlogs = client_qlogs if way == "download" else server_qlogs

        rcv_ref_time = int(rcv_qlogs['traces']
                            [0]['common_fields']['reference_time'])
        sdr_ref_time = int(sdr_qlogs['traces']
                            [0]['common_fields']['reference_time'])

        rcv_events = rcv_qlogs['traces'][0]['events']
        sdr_events = sdr_qlogs['traces'][0]['events']

        one_way_rtts = []
        timestamps = []
        pedding_1way_rtts = {}

        for rel_time, cat, evt, data in sdr_events:
            if evt == "packet_sent":
                if data["packet_type"] == "1RTT":
                    pkt_nbr = data['header']['packet_number']
                    pedding_1way_rtts[pkt_nbr] = sdr_ref_time+rel_time

        for rel_time, cat, evt, data in rcv_events:
            if evt == "packet_received":
                if data["packet_type"] == "1RTT":
                    pkt_nbr = data['header']['packet_number']
                    if pkt_nbr in pedding_1way_rtts:
                        timestamps.append((pedding_1way_rtts[pkt_nbr]-sdr_ref_time)/1000)
                        one_way_rtts.append(
                            ((rcv_ref_time + rel_time) - pedding_1way_rtts[pkt_nbr])/1000)

        return {
            'rtts': one_way_rtts,
            'timestamps': timestamps,
            'label': param['param']
        }
    except json.decoder.JSONDecodeError:
        print(f"WARNING : Error with folder {dir}")
        return None
