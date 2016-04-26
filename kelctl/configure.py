import json

import requests


def name(config, name):
    return dict(config, name=name)


def release(config, channel):
    config = dict(config)
    r = requests.get("https://storage.googleapis.com/release.kelproject.com/distro/channels.json")
    r.raise_for_status()
    channels = json.loads(r.content.decode("utf-8"))
    url = "https://storage.googleapis.com/release.kelproject.com/distro/{}/manifest.json"
    r = requests.get(url.format(channels[channel]))
    r.raise_for_status()
    config["release"] = json.loads(r.content.decode("utf-8"))
    return config


def gce(config, project_id, region, zone):
    config = dict(config)
    layer = config.setdefault("layer-0", {})
    layer["provider"] = {
        "type": "gce",
        "project-id": project_id,
        "region": region,
        "zone": zone,
    }
    return config


def resources_std(config):
    config = dict(config)
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
    return config
