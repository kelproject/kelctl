import json
import random
import string

import requests


def name(config, name):
    config["name"] = name


def domain(config, domain):
    config["domain"] = domain


def release(config, channel):
    r = requests.get("https://storage.googleapis.com/release.kelproject.com/distro/channels.json")
    r.raise_for_status()
    channels = json.loads(r.content.decode("utf-8"))
    r = requests.get(
        "https://storage.googleapis.com/release.kelproject.com/distro/{}/manifest.json".format(
            channels[channel]
        )
    )
    r.raise_for_status()
    config["release"] = json.loads(r.content.decode("utf-8"))
    config["release"].update({
        "channel": channel,
        "version": channels[channel],
    })


def gce(config, project_id, region, zone):
    layer = config.setdefault("layer-0", {})
    layer["provider"] = {
        "kind": "gce",
        "project-id": project_id,
        "region": region,
        "zone": zone,
    }


def layer0(config, pod_network, service_network, dns_service_ip):
    layer = config.setdefault("layer-0", {})
    layer["pod-network"] = pod_network
    layer["service-network"] = service_network
    layer["dns-service-ip"] = dns_service_ip


def layer1(config, identity_url, subdomain, router_ip, api_cache_disk_size, api_cache_disk_type, api_database_disk_size, api_database_disk_type):
    layer = config.setdefault("layer-1", {})
    layer.update({
        "identity-url": identity_url,
        "api": {
            "host": "{}.{}".format(subdomain, config["domain"]),
            "database": {
                "username": "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8)),
                "password": "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(32)),
                "name": "kel",
            },
        },
        "resources": {
            "router-ip": router_ip,
            "api-cache-disk": {
                "size": api_cache_disk_size,
                "type": api_cache_disk_type,
            },
            "api-database-disk": {
                "size": api_database_disk_size,
                "type": api_database_disk_type,
            }
        }
    })


# @@@ determine how to make this customizable
def resources_std(config, master_ip):
    layer = config.setdefault("layer-0", {})
    layer["resources"] = {
        "network": {
            "ipv4-range": "10.240.0.0/16"
        },
        "etcd": {
            "count": 3,
            "machine": {
                "type": "n1-standard-2",
                "boot-disk-type": "pd-standard",
                "boot-disk-size": 200,
                "data-disk": {
                    "type": "pd-ssd",
                    "size": 50
                }
            }
        },
        "master": {
            "machine-group": {
                "count": 3,
                "type": "n1-standard-2",
                "boot-disk-type": "pd-standard",
                "boot-disk-size": 200
            }
        },
        "nodes": [
            {
                "name": "node-1x",
                "max-pods": 30,
                "machine-group": {
                    "count": 3,
                    "type": "n1-standard-2",
                    "boot-disk-type": "pd-standard",
                    "boot-disk-size": 200
                }
            }
        ]
    }
    if master_ip:
        layer["resources"]["master-ip"] = master_ip
