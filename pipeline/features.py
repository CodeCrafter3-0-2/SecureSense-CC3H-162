import numpy as np

def extract_features(flow):
    duration = (flow.end_time - flow.start_time).total_seconds()
    duration = max(duration, 1e-6)

    packets = flow.total_packets
    bytes_ = flow.total_bytes

    avg_pkt = bytes_ / packets if packets > 0 else 0

    return {
        "Max Packet Length": avg_pkt,
        "Bwd Packet Length Min": 0,
        "Idle Mean": duration,
        "PSH Flag Count": 0,
        "Idle Min": duration,
        "Bwd Packet Length Mean": 0,
        "Min Packet Length": avg_pkt,
        "act_data_pkt_fwd": packets,
        "Bwd Header Length": 0,
        "Total Fwd Packets": packets,
        "Packet Length Mean": avg_pkt,
        "Destination Port": 80,  # default HTTP (you can parse later)
        "min_seg_size_forward": avg_pkt,
        "Flow Duration": duration,
        "Active Max": duration,
        "Bwd Packet Length Std": 0,
        "Fwd Header Length": packets * 20,  # rough TCP header estimate
        "Init_Win_bytes_backward": 0,
        "FIN Flag Count": 0,
        "ACK Flag Count": packets
    }