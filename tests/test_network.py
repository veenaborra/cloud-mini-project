"""Subnets are minimal and contiguous; NACL passes the sample packets."""
import ipaddress, json
import nacl_sim

PLAN = [("10.20.0.0/22", 1000), ("10.20.4.0/24", 250), ("10.20.5.0/25", 100), ("10.20.5.128/27", 20)]


def test_subnets():
    nxt = ipaddress.ip_address("10.20.0.0")
    for cidr, need in PLAN:
        net = ipaddress.ip_network(cidr)
        assert net.network_address == nxt
        assert net.num_addresses - 2 >= need > net.num_addresses // 2 - 2
        nxt = net.broadcast_address + 1


def test_nacl_samples():
    rules = nacl_sim.load_rules("network/nacl.json")
    for line in open("network/packets_sample.jsonl"):
        p = json.loads(line)
        assert nacl_sim.decide(rules, p)[0] == p["expected"]
