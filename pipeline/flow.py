flows = {}

class Flow:
    def __init__(self, log):
        self.src_ip = log["src_ip"]
        self.endpoint = log["endpoint"]

        self.start_time = log["timestamp"]
        self.end_time = log["timestamp"]

        self.total_packets = 1
        self.total_bytes = log["bytes"]

    def update(self, log):
        self.end_time = log["timestamp"]
        self.total_packets += 1
        self.total_bytes += log["bytes"]


def get_flow_key(log):
    return (log["src_ip"], log["endpoint"])


def update_flow(log):
    key = get_flow_key(log)

    if key not in flows:
        flows[key] = Flow(log)
    else:
        flows[key].update(log)

    return flows[key]