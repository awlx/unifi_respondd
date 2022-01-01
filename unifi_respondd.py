#!/usr/bin/env python3

from unificontrol import UnifiClient
from typing import List
from geopy.geocoders import Nominatim
import time
import dataclasses
import config


@dataclasses.dataclass
class Accesspoint:
    name: str
    mac: str
    snmp_location: str
    client_count: int
    latitude: float
    longitude: float


@dataclasses.dataclass
class Accesspoints:
    accesspoints: List[Accesspoint]


def get_sites(cfg):
    """This function returns a list of sites."""
    client = UnifiClient(
        host=cfg.controller_url,
        port=cfg.controller_port,
        username=cfg.username,
        password=cfg.password,
        cert=None,
    )
    client.login()
    sites = client.list_sites()
    return sites


def get_aps(cfg, site):
    """This function returns a list of APs."""
    client = UnifiClient(
        host=cfg.controller_url,
        port=cfg.controller_port,
        username=cfg.username,
        password=cfg.password,
        cert=None,
        site=site,
    )
    client.login()
    aps = client.list_devices()
    return aps


def get_clients_for_site(cfg, site):
    client = UnifiClient(
        host=cfg.controller_url,
        port=cfg.controller_port,
        username=cfg.username,
        password=cfg.password,
        cert=None,
        site=site,
    )
    client.login()
    clients = client.list_clients()
    return clients


def get_client_count_for_ap(ap_mac, clients):
    client_count = 0
    for client in clients:
        if client.get("ap_mac", "No mac") == ap_mac:
            client_count += 1
    return client_count


def get_location_by_address(address, app):
    """This function returns latitude and longitude of a given address."""
    time.sleep(1)
    try:
        return app.geocode(address).raw["lat"], app.geocode(address).raw["lon"]
    except:
        return get_location_by_address(address)


def get_infos():
    cfg = config.Config.from_dict(config.load_config())
    geolookup = Nominatim(user_agent="ffmuc_respondd")
    aps = Accesspoints(accesspoints=[])
    for site in get_sites(cfg):
        aps_for_site = get_aps(cfg, site["name"])
        clients = get_clients_for_site(cfg, site["name"])
        for ap in aps_for_site:
            if ap.get("name", None) is not None:
                lat, lon = 0, 0
                if ap.get("snmp_location", None) is not None:
                    try:
                        lat, lon = get_location_by_address(ap["snmp_location"], geolookup)
                    except:
                        pass

                aps.accesspoints.append(
                    Accesspoint(
                        name=ap.get("name", None),
                        mac=ap.get("mac", None),
                        snmp_location=ap.get("snmp_location", None),
                        client_count=get_client_count_for_ap(ap.get("mac", None), clients),
                        latitude=float(lat),
                        longitude=float(lon),
                    )
                )
    return aps


def main():
    print(get_infos())


if __name__ == "__main__":
    main()
