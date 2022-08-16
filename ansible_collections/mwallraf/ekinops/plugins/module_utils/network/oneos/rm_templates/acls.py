# -*- coding: utf-8 -*-
# Copyright 2022 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

"""
The Acls parser templates file. This contains
a list of parser definitions and associated functions that
facilitates both facts gathering and native command generation for
the given network resource.
"""

import re
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.rm_base.network_template import (
    NetworkTemplate,
)


def _tmplt_access_list_entries(aces):
    def source_destination_common_config(config_data, command, attr):
        if config_data[attr].get("address"):
            command += " {address}".format(**config_data[attr])
            if config_data[attr].get("wildcard_bits"):
                command += " {wildcard_bits}".format(**config_data[attr])
        elif config_data[attr].get("any"):
            command += " 0.0.0.0 255.255.255.255".format(**config_data[attr])
        elif config_data[attr].get("host"):
            command += " {host} 0.0.0.0".format(**config_data[attr])
        if config_data[attr].get("port_protocol"):
            if config_data[attr].get("port_protocol").get("range"):
                command += " {0} {1}".format(
                    config_data[attr]["port_protocol"]["range"].get("start"),
                    config_data[attr]["port_protocol"]["range"].get("end"),
                )
            else:
                port_proto_type = list(
                    config_data[attr]["port_protocol"].keys(),
                )[0]
                command += " {1}".format(
                    config_data[attr]["port_protocol"][port_proto_type],
                )
        return command

    command = " "
    proto_option = None

    if aces:
        # if aces.get("sequence") and aces.get("afi") == "ipv4":
        #     command += "{sequence}".format(**aces)
        # if (
        #     aces.get("grant")
        #     # and aces.get("sequence")
        #     and aces.get("afi") == "ipv4"
        # ):
        #     command += "{grant}".format(**aces)
        # elif (
        #     aces.get("grant")
        #     # and aces.get("sequence")
        #     and aces.get("afi") == "ipv6"
        # ):
        #     command += "{grant}".format(**aces)
        # elif aces.get("grant"):
        #     command += "{grant}".format(**aces)

        if aces.get("grant"):
            command += "{grant}".format(**aces)

        if aces.get("protocol_options"):
            command += " {protocol}".format(**aces["protocol_options"])

            if "protocol_number" in aces["protocol_options"]:
                command += " {protocol_number}".format(
                    **aces["protocol_options"]
                )

        # if aces.get("protocol_options"):
        #     if "protocol_number" in aces["protocol_options"]:
        #         command += " {protocol_number}".format(
        #             **aces["protocol_options"]
        #         )
        #     else:
        #         command += " {0}".format(list(aces["protocol_options"])[0])
        #         proto_option = aces["protocol_options"].get(
        #             list(aces["protocol_options"])[0],
        #         )
        # elif aces.get("protocol"):
        #     command += " {protocol}".format(**aces)

        if aces.get("source"):
            command = source_destination_common_config(aces, command, "source")

        if aces.get("destination"):
            command = source_destination_common_config(
                aces,
                command,
                "destination",
            )

        if aces.get("protocol_options"):
            icmp_message_type = aces["protocol_options"].get(
                "icmp_message_type"
            )
            icmp_message_code = aces["protocol_options"].get(
                "icmp_message_code"
            )

            if icmp_message_type:
                command += " {}".format(icmp_message_type)

            if icmp_message_code:
                command += " {}".format(icmp_message_code)

        if aces.get("dscp"):
            command += " dscp {dscp}".format(**aces)

        # if isinstance(proto_option, dict):
        #     command += " {0}".format(
        #         list(proto_option.keys())[0],
        #     )

        if aces.get("log"):
            command += " log"
            if aces["log"].get("user_cookie"):
                command += " {user_cookie}".format(**aces["log"])

        if aces.get("fragments"):
            command += " fragments"

        if aces.get("reflexive"):
            command += " reflexive"

        if aces.get("precedence"):
            command += " precedence {precedence}".format(**aces)

        if aces.get("sequence"):
            command += " sequence {sequence}".format(**aces)

        # if aces.get("log_input"):
        #     command += " log-input"
        #     if aces["log_input"].get("user_cookie"):
        #         command += " {user_cookie}".format(**aces["log_input"])

        # if aces.get("option"):
        #     option_val = list(aces.get("option").keys())[0]
        #     command += " option {0}".format(option_val)

    return command


class AclsTemplate(NetworkTemplate):
    def __init__(self, lines=None, module=None):
        super(AclsTemplate, self).__init__(
            lines=lines, tmplt=self, module=module
        )

    # fmt: off
    PARSERS = [
        {
            "name": "acls_name",
            "getval": re.compile(
                r"""^(?P<afi>IP|IPv6|ip|ipv6|IP|IPv6)
                \saccess[\s-]list
                \s*(?P<acl_type>standard|extended)*
                \s*(?P<acl_name>.+)*
                """,
                re.VERBOSE,
            ),
            "compval": "name",
            "setval": "name",
            "result": {
                "acls": {
                    "{{ acl_name|d() }}": {
                        "name": "{{ acl_name }}",
                        "acl_type": "{{ acl_type.lower() if acl_type is defined }}",
                        "afi": "{{ 'ipv6' if 'v6' in afi else 'ipv4' }}",
                    },
                },
            },
            "shared": True,
        },
        {
            "name": "_acls_name",
            "getval": re.compile(
                r"""^(ip|ipv6)-remark
                    \saccess-list
                    \s*(standard|extended)*
                    \s(?P<acl_name_r>\S+)?
                    $""",
                re.VERBOSE,
            ),
            "compval": "name",
            "setval": "ip access-list",
            "result": {},
            "shared": True,
        },
        {
            "name": "remarks",
            "getval": re.compile(
                r"""\s+remark
                    (\s*(?P<remarks>.+))?
                    $""",
                re.VERBOSE,
            ),
            "setval": "remark {{ remarks }}",
            "result": {
                "acls": {
                    "{{ acl_name_r|d() }}": {
                        "name": "{{ acl_name_r }}",
                        "aces": [{"remarks": "{{ remarks }}"}],
                    },
                },
            },
        },
        {
            "name": "aces",
            "getval": re.compile(
                r"""
                ^(?:\s+(?P<startsequence>\d+)\s)?
                \s*(?P<grant>permit|deny)
                (?:\s(?P<protocol>ip|tcp|udp|gre|icmp|protocol\snumber\s(?P<protocol_num>\d+)))?
                (?:\sicmp-type\s(?P<icmp_type>\d+))?(?:\sicmp-code\s(?P<icmp_code>\d+))?
                (?:\s(?P<source>any|host\s\d+\.\d+\.\d+.\d+|\d+\.\d+\.\d+.\d+\s\d+\.\d+\.\d+.\d+|\d+\.\d+\.\d+.\d+))
                (?:\s(?:(?P<source_port>eq\s\d+)|range\s(?P<srange_start>\d+)\s(?P<srange_end>\d+)))?
                (?:\s(?P<destination>any|host\s\d+\.\d+\.\d+.\d+|\d+\.\d+\.\d+.\d+\s\d+\.\d+\.\d+.\d+))?
                (?:\s(?:(?P<destination_port>eq\s\d+)|range\s(?P<drange_start>\d+)\s(?P<drange_end>\d+))?)?
                (?:\sdscp\s(?P<dscp>\d+))?
                (?:\s(?P<log>log))?
                (?:\s(?P<reflexive>reflexive))?
                (?:\s(?P<fragments>fragments))?
                (?:\ssequence\s(?P<endsequence>\d+))?
                (?:\s\(\d+\smatches\))?
                $
                """,
                re.VERBOSE,
            ),
            "compval": "aces",
            "setval": _tmplt_access_list_entries,
            "result": {
                "acls": {
                    "{{ acl_name|d() }}": {
                        "name": "{{ acl_name }}",
                        "aces": [
                            {
                                "sequence": "{{ startsequence if startsequence else endsequence if endsequence else None }}",
                                "grant": "{{ grant }}",
                                "protocol": "{% if 'number' in protocol %}ip{% elif protocol %}{{ protocol }}{% endif %}",
                                "protocol_number": "{{ protocol_num }}",
                                "icmp_message_type": "{{ icmp_type }}",
                                "icmp_message_code": "{{ icmp_code }}",
                                "source": {
                                    "address": "{% if source is defined and '.' in source and 'host' not in source %}{{\
                                        source.split(' ')[0] }}{% elif source is defined and '::' in source %}{{ source }}{% endif %}",
                                    "wildcard_bits": "{{ source.split(' ')[1] if source is defined and ' ' in source and '.' in source and 'host' not in source }}",
                                    "any": "{{ True if source is defined and source == 'any' }}",
                                    "host": "{{ source.split(' ')[1] if source is defined and 'host' in source }}",
                                    "port_protocol": {
                                        "{{ source_port.split(' ')[0] if source_port is defined else None }}": "{{\
                                            source_port.split(' ')[1] if source_port is defined else None }}",
                                        "range": {
                                            "start": "{{ srange_start if srange_start is defined else None }}",
                                            "end": "{{ srange_end if srange_end is defined else None }}",
                                        },
                                    },
                                    },
                                "destination": {
                                    "address": "{% if destination is defined and '.' in destination and 'host' not in destination %}{{\
                                        destination.split(' ')[0] }}{% elif destination is defined and '::' in destination %}{{ destination }}{% endif %}",
                                    "wildcard_bits": "{{ destination.split(' ')[1] if destination is defined and ' ' in destination and '.' in destination and 'host' not in destination }}",
                                    "any": "{{ True if destination is defined and destination == 'any' }}",
                                    "host": "{{ destination.split(' ')[1] if destination is defined and 'host' in destination }}",
                                    "port_protocol": {
                                        "{{ dest_port.split(' ')[0] if dest_port is defined else None }}": "{{\
                                            dest_port.split(' ')[1] if dest_port is defined else None }}",
                                        "range": {
                                            "start": "{{ drange_start if drange_start is defined else None }}",
                                            "end": "{{ drange_end if drange_end is defined else None }}",
                                        },
                                    },

                                    },
                                "log": "{{ not not log }}",
                                "precedence": "{{ precedence if precedence is defined else None }}",
                                "dscp": "{{ True if dscp is defined else None }}",
                                "fragments": "{{ True if fragments is defined else None }}",
                                "reflexive": "{{ True if reflexive is defined else None }}",
                            },
                        ],
                    },
                },
            },
        },
    ]

    # fmt: on
