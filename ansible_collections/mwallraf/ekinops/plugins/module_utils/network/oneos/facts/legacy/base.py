#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
The ios legacy fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type


import platform
import re

from ansible_collections.mwallraf.ekinops.plugins.module_utils.network.oneos.oneos import (  # noqa:E501
    run_commands,
    get_capabilities,
    get_oneos_version,
)
from ansible_collections.mwallraf.ekinops.plugins.module_utils.network.oneos.utils.commands import (  # noqa:E501
    OneosCommand,
)

from datetime import datetime
from ansible.module_utils.six import iteritems


class FactsBase(object):

    COMMANDS = list()

    def __init__(self, module):
        self.module = module
        self.facts = dict()
        self.warnings = list()
        self.responses = None
        self._oneos_version = None
        self._oneos_command_class = None

    @property
    def oneos_version(self):
        if not self._oneos_version:
            self._oneos_version = int(get_oneos_version(self.module))
        return self._oneos_version

    def init(self):
        self._oneos_command_class = OneosCommand(self.oneos_version)

    def populate(self):
        self.responses = run_commands(
            self.module, commands=self.COMMANDS, check_rc=False
        )

    def run(self, cmd):
        return run_commands(self.module, commands=cmd, check_rc=False)


class Default(FactsBase):
    """Gets information from connection get_capabilities info"""

    COMMANDS = []

    def populate(self):
        super(Default, self).populate()
        self.facts.update(self.platform_facts())

    def platform_facts(self):
        platform_facts = {}

        resp = get_capabilities(self.module)
        device_info = resp["device_info"]
        self._oneos_version = device_info.get("network_os_version", None)

        platform_facts["system"] = device_info["network_os"]

        for item in (
            "model",
            "vendor",
            "version",
            "hostname",
            "serial_number",
            "supports_wifi",
            "supports_cellular",
            "supports_voip_codecs",
            "local_interfaces",
            "uplink_interfaces",
        ):
            val = device_info.get("network_os_%s" % item)
            if val is not None:
                platform_facts[item] = val

        platform_facts["api"] = resp["network_api"]
        platform_facts["python_version"] = platform.python_version()

        return platform_facts


class Hardware(FactsBase):
    def __init__(self, module):
        super(Hardware, self).__init__(module)

        self.init()
        # get OS specific fact commands
        self.COMMANDS = self._oneos_command_class.facts_hardware_commands

    def populate(self):
        super(Hardware, self).populate()

        data = self.responses[0]
        if data:
            self.facts["uptime"] = self.parse_system_info(data)
            self.facts["software"] = self.parse_software_info(data)

        data = self.responses[2]
        if data:
            self.facts["memory"] = self.parse_memory(data)

        eval(f"self.populate_V{self.oneos_version}()")

        mandatory_keys = [
            "uptime",
            "software",
            "memory",
            "cpu",
            "filesystems",
            "boot",
        ]
        for mandatory_key in mandatory_keys:
            if not self.facts.get(mandatory_key):
                self.facts[mandatory_key] = ""
                self.warnings.append(
                    f"Unable to gather {mandatory_key} statistics"
                )

    def populate_V5(self):
        data = self.responses[0]
        if data:
            self.facts["cpu"] = self.parse_cpu_V5(data)

        data = self.responses[1] + self.responses[6] + self.responses[7]
        if data:
            self.facts["filesystems"] = self.parse_filesystems_info_V5(data)

        data = [self.responses[3], self.responses[4], self.responses[5]]
        self.facts["boot"] = self.parse_boot_info_V5(data)

    def populate_V6(self):
        data = self.responses[0]
        if data:
            self.facts["cpu"] = self.parse_cpu_V6(data)

        data = self.responses[2]
        if data:
            self.facts["filesystems"] = self.parse_filesystems_info_V6(data)

        data = [self.responses[3], self.responses[4], self.responses[5]]
        self.facts["boot"] = self.parse_boot_info_V6(data)

    def parse_boot_info_V5(self, datas):
        facts = dict()

        facts["supports_alternate_banks"] = False

        data = datas[0]
        match = re.search(
            r"""^(?P<BOOTDRIVE>.*):(?P<BOOTIMAGEFOLDER>\/BSA\/binaries)
            \/(?P<BOOTFILE>\S+)$""",
            data,
            re.M | re.VERBOSE,
        )
        if match:
            facts["image_drive"] = match.group(1)
            facts["image_folder"] = match.group(2)
            facts["image_name"] = match.group(3)

        match = re.search(
            r"""^(?P<BOOTDRIVE>.*):(?P<BOOTCONFIGFOLDER>\/BSA\/config)
            \/(?P<BOOTCONFIG>\S+)$""",
            data,
            re.M | re.VERBOSE,
        )
        if match:
            facts["config_drive"] = match.group(1)
            facts["config_folder"] = match.group(2)
            facts["config_name"] = match.group(3)

        data = datas[1]
        matches = re.finditer(r"\W+(\S+)\s+([0-9]{2,})$", data, re.M)
        if matches:
            boot_files = []
            for matchNum, match in enumerate(matches, start=1):
                boot_files.append(
                    {"file": match.group(1), "size_bytes": match.group(2)}
                )
            facts["available_images"] = boot_files

        data = datas[2]
        matches = re.finditer(r"\W+(\S+)\s+([0-9]{2,})$", data, re.M)
        if matches:
            boot_files = []
            for matchNum, match in enumerate(matches, start=1):
                boot_files.append(
                    {"file": match.group(1), "size_bytes": match.group(2)}
                )
            facts["available_configs"] = boot_files

        return facts

    def parse_boot_info_V6(self, datas):
        facts = dict()

        facts["supports_alternate_banks"] = True
        facts["image_folder"] = "/BSA/binaries"
        facts["config_folder"] = "/BSA/config"
        facts["config_name"] = "bsaStart.cfg"
        facts["software_banks"] = dict()

        data = datas[0]
        matches = re.finditer(
            r"^\S+\s+\d+\s+(\d+)\s+\S+\s+\S+\s+\S+\s+(\S+)", data, re.M
        )
        if matches:
            files = []
            for matchNum, match in enumerate(matches, start=1):
                files.append(
                    {"file": match.group(2), "size_bytes": match.group(1)}
                )
            facts["available_images"] = files

        data = datas[1]
        matches = re.finditer(
            r"^\S+\s+\d+\s+(\d+)\s+\S+\s+\S+\s+\S+\s+(\S+)", data, re.M
        )
        if matches:
            files = []
            for matchNum, match in enumerate(matches, start=1):
                files.append(
                    {"file": match.group(2), "size_bytes": match.group(1)}
                )
            facts["available_configs"] = files

        bank = None
        image = None
        checksum = None
        for line in datas[2].split("\n"):
            m = re.match(r"\W+(\w+)\sbank\W+", line)
            if m:
                bank = m.group(1).lower()

            m = re.match(r"Software\sversion\s+:\s+(.*)", line)
            if m:
                image = m.group(1)

            m = re.match(r"Header\schecksum\s+:\s+(.*)", line)
            if m:
                checksum = m.group(1)

            if image and bank and checksum:
                current_image = [
                    curr["file"]
                    for curr in facts.get("available_images", [])
                    if curr["file"].startswith(image)
                ]
                if bank == "active" and current_image:
                    facts["image_name"] = current_image[0]
                facts["software_banks"][bank] = {
                    "image": image,
                    "checksum": checksum,
                }
                image = bank = checksum = None

        return facts

    def parse_software_info(self, data):
        facts = dict()

        match = re.search(r"\W*Software [Vv]ersion\W+(\S+)\W*$", data, re.M)
        if match:
            facts["software_version"] = match.group(1)

        match = re.search(r"\W*Boot [Vv]ersion\W+(\S+)\W*$", data, re.M)
        if match:
            facts["boot_version"] = match.group(1)

        match = re.search(r"\W*Recovery version\W+(\S+)\W*$", data, re.M)
        if match:
            facts["recovery_version"] = match.group(1)
            facts["supports_alternate_version"] = True
        else:
            facts["supports_alternate_version"] = False

        match = re.search(r"\W*License token\W+(\S+)\W*$", data, re.M)
        if match and match.group(1) != "None":
            facts["license"] = match.group(1)

        return facts

    def parse_system_info(self, data):
        facts = dict()

        def _convert_datetime_to_iso(dt):
            """oneos has 2 formats:
            1) %d/%m/%y %H:%M:%S
            2) %Y-%m-%d %H:%M:%S%z
            """
            if "-" in dt:
                _dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S%z")
            else:
                _dt = datetime.strptime(dt, "%d/%m/%y %H:%M:%S")
            if _dt:
                return _dt.isoformat()
            return _dt

        match = re.search(r"\W*System started\W+(.*)$", data, re.M)
        if match:
            started_at = _convert_datetime_to_iso(match.group(1))
            facts["started_at"] = started_at

        match = re.search(r"\W*Sys Up time\W+(.*)$", data, re.M)
        if match:
            facts["uptime"] = match.group(1)

        if facts.get("uptime"):
            match = re.search(
                r"""(?:(?P<DAYS>\d+)d\W*)?(?:(?P<HOURS>\d+)h\W*)?
                (?:(?P<MINUTES>\d+)m\W*)?(?:(?P<SECONDS>\d+)s)?""",
                facts["uptime"],
                re.VERBOSE,
            )
            if match:
                total_seconds = (
                    int(match.groupdict().get("DAYS", 0)) * 86400
                    + int(match.groupdict().get("HOURS", 0)) * 3600
                    + int(match.groupdict().get("MINUTES", 0)) * 60
                    + int(match.groupdict().get("SECONDS", 0))
                )
                facts["uptime_seconds"] = int(total_seconds)

        match = re.search(r"\W*Current system time\W+(.*)$", data, re.M)
        if match:
            system_time = _convert_datetime_to_iso(match.group(1))
            facts["system_time"] = system_time

        match = re.search(r"\W*Start caused by\W+(.*)$", data, re.M)
        if match:
            facts["restart_cause"] = match.group(1)

        return facts

    def parse_memory(self, data):
        facts = dict()

        m = re.search(
            r"""System total\W+(?P<TOTAL>[\d+ ]+\d).*\n.*\s+used\W+
            (?P<USED>[\d+ ]+\d)\W+(?P<USEDPCT>[\S]+)%.*\n.*\s+free
            \W+(?P<FREE>[\d+ ]+\d)\W+(?P<FREEPCT>[\S]+)%""",
            data,
            re.M | re.VERBOSE,
        )
        if m:
            mem_total_kb = float(m.groupdict()["TOTAL"].replace(" ", ""))
            mem_used_kb = float(m.groupdict()["USED"].replace(" ", ""))
            mem_used_pct = float(m.groupdict()["USEDPCT"])
            mem_free_kb = float(m.groupdict()["FREE"].replace(" ", ""))
            mem_free_pct = float(m.groupdict()["FREEPCT"])

            facts["mem_free_mb"] = int(mem_free_kb / 1024)
            facts["mem_used_mb"] = int(mem_used_kb / 1024)
            facts["mem_total_mb"] = int(mem_total_kb / 1024)
            facts["mem_free_pct"] = float(mem_used_pct)
            facts["mem_used_pct"] = float(mem_free_pct)

        m = re.search(r"Memory Total\W+(?P<TOTAL>\d+)", data, re.M)
        if m:
            mem_total_b = float(m.groupdict()["TOTAL"])
            facts["mem_total_mb"] = int(mem_total_b / (1024 * 1024))

        return facts

    def parse_cpu_V5(self, data):
        facts = list()

        all_cpu = re.findall(
            r"""Core (?P<cpu>\d+).*\nAverage CPU load.*\/\W*
            (?P<avg_load>[\d\.]+)%""",
            data,
            re.M | re.VERBOSE,
        )

        for cpu in all_cpu:
            facts.append(
                {"cpu": f"Core {cpu[0]}", "avg_load_pct": float(cpu[1])}
            )

        return facts

    def parse_cpu_V6(self, data):
        facts = list()

        all_cpu = re.findall(
            r"""^\W+(\d+)\W+(?:control|forwarding)
            [^%]+%[^%]+%[^%]+%\W+([\d\.]+)\W%""",
            data,
            re.M | re.VERBOSE,
        )

        for cpu in all_cpu:
            facts.append(
                {"cpu": f"Core {cpu[0]}", "avg_load_pct": float(cpu[1])}
            )

        return facts

    def parse_filesystems(self, data):
        # example output: [('Ram', '1'), ('Flash', '256')]
        return re.findall(r"\s+(\S+)\s+disk\s+:\s*(\d+)M[Bo]", data, re.M)

    def parse_filesystems_info_V5(self, data):
        allfs = self.parse_filesystems(data)
        fs_details = {
            fs[0].lower(): {
                "spacetotal_kb": int(fs[1]) * 1024,
                "spacetotal_mb": int(fs[1]),
            }
            for fs in allfs
        }

        facts = dict()

        fs = None
        for line in data.split("\n"):
            # find the filesystem
            match = re.match(r"^.*devHdr.name:\s+(\S+?)(?:disk)?:", line)
            if match:
                fs = match.group(1).lower()
                if fs and fs in fs_details:
                    facts[fs] = fs_details[fs]
                else:
                    fs = None
                continue
            # find the free disk space
            match = re.match(
                r"^.*free space on volume:\s+(\S+?)\sbytes.*", line
            )
            if match and fs:
                facts[fs]["spacefree_kb"] = (
                    int(match.group(1).replace(",", "")) / 1024
                )
                facts[fs]["spacefree_pct"] = int(
                    (facts[fs]["spacefree_kb"] / facts[fs]["spacetotal_kb"])
                    * 100
                )
                continue

        return facts

    def parse_filesystems_info_V6(self, data):
        facts = dict()

        m = re.search(
            r"""^.*user\D+(?P<total_b>\d+)\D+
            (?P<free_b>\d+)\D+(?P<used_pct>[\d\.]+)%""",
            data,
            re.M | re.VERBOSE,
        )
        if m:
            flash_total_b = float(m.groupdict()["total_b"])
            flash_free_b = float(m.groupdict()["free_b"])
            flash_used_pct = float(m.groupdict()["used_pct"])
            flash_free_pct = 100 - flash_used_pct

            facts["flash"] = dict()
            facts["flash"]["spacetotal_kb"] = int(flash_total_b / 1024)
            facts["flash"]["spacetotal_mb"] = int(
                flash_total_b / (1024 * 1024)
            )
            facts["flash"]["spacefree_kb"] = int(flash_free_b / 1024)
            facts["flash"]["spacefree_pct"] = int(flash_free_pct)

        return facts


class Config(FactsBase):

    COMMANDS = ["show running-config"]

    def populate(self):
        super(Config, self).populate()
        data = self.responses[0]
        if data:
            data = re.sub(
                """Building configuration...\n\nCurrent configuration: \n\n""",
                "",
                data,
                flags=re.MULTILINE,
            )
            self.facts["config"] = data


class Interfaces(FactsBase):

    COMMANDS = [
        "show interfaces",
        # "show ip interface",
        # "show ipv6 interface",
    ]

    IGNORE_INTERFACES = ["Null", "null"]

    def populate(self):
        super(Interfaces, self).populate()

        self.facts["all_ipv4_addresses"] = list()
        self.facts["all_ipv6_addresses"] = list()

        data = self.responses[0]
        if data:
            interfaces = self.parse_interfaces(data)
            self.facts["interfaces"] = self.populate_interfaces(interfaces)

        # data = self.responses[1]
        # if data:
        #     data = self.parse_interfaces(data)
        #     self.populate_ipv4_interfaces(data)

        # data = self.responses[2]
        # if data:
        #     data = self.parse_interfaces(data)
        #     self.populate_ipv6_interfaces(data)

    def populate_interfaces(self, interfaces):
        facts = dict()
        for key, value in iteritems(interfaces):
            for intf in self.IGNORE_INTERFACES:
                if key.startswith(intf):
                    continue

            intf = dict()
            intf["description"] = self.parse_description(value)
            intf["macaddress"] = self.parse_macaddress(value)

            intf["mtu"] = self.parse_mtu(value)
            intf["bandwidth"] = self.parse_bandwidth(value)
            intf["mediatype"] = self.parse_mediatype(value)
            intf["duplex"] = self.parse_duplex(value)
            intf["speed"] = self.parse_speed(value)
            intf["lineprotocol"] = self.parse_lineprotocol(value)
            intf["operstatus"] = self.parse_operstatus(value)
            intf["type"] = self.parse_type(value)
            intf["vrf"] = self.parse_vrf(value)
            intf["flags"] = self.parse_flags(value)

            intf["ipv4"] = self.populate_ipv4_interfaces(value)
            intf["ipv6"] = self.populate_ipv6_interfaces(value)

            facts[key] = intf
        return facts

    def populate_ipv4_interfaces(self, data):
        facts = list()

        primary_address = addresses = []
        primary_address = re.findall(
            r"Internet address is (\d+\.\d+\.\d+\.\d+\/\d+).*$",
            data,
            re.M,
        )
        addresses = re.findall(
            r"Secondary address is (\d+\.\d+\.\d+\.\d+\/\d+).*$", data, re.M
        )
        if len(primary_address) == 0:
            return facts
        addresses = primary_address + addresses
        for idx, address in enumerate(addresses):
            addr, subnet = address.split("/")
            ipv4 = dict(
                address=addr.strip(),
                subnet=subnet.strip(),
                primary=(True if idx == 0 else False),
            )
            self.add_ip_address(f"{addr.strip()}/{subnet.strip()}", "ipv4")
            facts.append(ipv4)

        return facts

    def populate_ipv6_interfaces(self, data):
        facts = list()

        addresses = re.findall(r"IPv6 address is (\S+\/\d+)", data, re.M)
        for address in addresses:
            addr, subnet = address.split("/")
            ipv6 = dict(address=addr.strip(), subnet=subnet.strip())
            self.add_ip_address(address.strip(), "ipv6")
            facts.append(ipv6)
        return facts

    def add_ip_address(self, address, family):
        if family == "ipv4":
            self.facts["all_ipv4_addresses"].append(address)
        else:
            self.facts["all_ipv6_addresses"].append(address)

    def parse_interfaces(self, data):
        parsed = dict()
        key = ""
        for line in data.split("\n"):
            if len(line) == 0:
                continue
            if line[0] == " ":
                parsed[key] += "\n%s" % line
            else:
                match = re.match(r"^(\w+\s?\S+) is.*", line)
                if match:
                    key = match.group(1)
                    parsed[key] = line
        return parsed

    def parse_description(self, data):
        match = re.search(r"Description: (.+)$", data, re.M)
        if match:
            return match.group(1)

    def parse_macaddress(self, data):
        match = re.search(r"Hardware address is (\S+), ARP.*", data)
        if match:
            return match.group(1)

    def parse_ipv4(self, data):
        match = re.search(r"Internet address is (\S+)", data)
        if match:
            addr, masklen = match.group(1).split("/")
            return dict(address=addr, masklen=int(masklen))

    def parse_mtu(self, data):
        match = re.search(r", (?:IPv4 )?MTU (\d+)", data)
        if match:
            return int(match.group(1))

    def parse_bandwidth(self, data):
        match = re.search(r"bandwidth limit (\d+) kbps", data)
        if match:
            return int(match.group(1))

    def parse_duplex(self, data):
        match = re.search(r", ((?:\w+-)?duplex(?:[ -]\w+)?)", data, re.M)
        if match:
            return match.group(1)

    def parse_mediatype(self, data):
        match = re.search(r"media-type (.+)$", data, re.M)
        if match:
            return match.group(1)

    def parse_type(self, data):
        match = re.search(r"Hardware is (.+),", data, re.M)
        if match:
            return match.group(1)

    def parse_lineprotocol(self, data):
        match = re.search(r"line protocol is (up|down)(.+)?$", data, re.M)
        if match:
            return match.group(1)

    def parse_operstatus(self, data):
        match = re.search(r"^(?:.+) is (.+), line protocol", data, re.M)
        if match:
            return match.group(1)

    def parse_vrf(self, data):
        match = re.search(r"associated to VRF (\w+)", data, re.M)
        if match:
            return match.group(1)

    def parse_flags(self, data):
        match = re.search(r"Flags:\s\(\S+\)\s(.*),", data, re.M)
        if match:
            return match.group(1).split(" ")

    def parse_speed(self, data):
        match = re.search(r"Line speed (\d+) kbps", data, re.M)
        if match:
            return int(match.group(1))
