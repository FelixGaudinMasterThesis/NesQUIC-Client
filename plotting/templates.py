from utils import get_info_rtts_cdf, plot_rtts_cdf
from utils import get_info_rtts_evolution, plot_rtts_evolution
from utils import get_info_smoothed_rtts_evolution
from utils import get_info_comp_table, plot_comp_table
from utils import get_info_complet, plot_complet
from utils import get_info_one_way_rtt

templates = {
    "rtts_cdf": {
        "get_data": get_info_rtts_cdf,
        "plot_data": plot_rtts_cdf,
        "xlabel": 'RTT (ms)',
        "ylabel": 'CDF'
    },
    "rtts_evolution": {
        "get_data": get_info_rtts_evolution,
        "plot_data" : plot_rtts_evolution,
        "xlabel": 'Time (s)',
        "ylabel": 'Latest RTT (ms)'
    },
    "smoothed_rtts_evolution": {
        "get_data": get_info_smoothed_rtts_evolution,
        "plot_data": plot_rtts_evolution,
        "xlabel": 'Time (s)',
        "ylabel": 'Latest RTT (ms)'
    },
    "comp_table" : {
        "get_data" : get_info_comp_table,
        "plot_data" : plot_comp_table,
        "figsize": (20, 10)
    },
    "complet" : {
        "get_data" : get_info_complet,
        "plot_data": plot_complet,
        "figsize": (30, 10)
    },
    "one_way_rtts_cdf": {
        "get_data": get_info_one_way_rtt,
        "plot_data": plot_rtts_cdf,
        "xlabel": '1-Way RTT (ms)',
        "ylabel": 'CDF'
    },
    "one_way_rtts_evolution": {
        "get_data": get_info_one_way_rtt,
        "plot_data": plot_rtts_evolution,
        "xlabel": 'Time (s)',
        "ylabel": '1-Way RTT (ms)'
    }
}
