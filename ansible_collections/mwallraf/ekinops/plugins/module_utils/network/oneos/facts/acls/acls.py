# -*- coding: utf-8 -*-
# Copyright 2022 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

"""
The oneos acls fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""

from copy import deepcopy
import re

from ansible.module_utils.six import iteritems
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common import (
    utils,
)
from ansible_collections.mwallraf.ekinops.plugins.module_utils.network.oneos.rm_templates.acls import (
    AclsTemplate,
)
from ansible_collections.mwallraf.ekinops.plugins.module_utils.network.oneos.argspec.acls.acls import (
    AclsArgs,
)


class AclsFacts(object):
    """The oneos acls facts class"""

    def __init__(self, module, subspec="config", options="options"):
        self._module = module
        self.argument_spec = AclsArgs.argument_spec

    def get_acl_data(self, connection):
        # Get the access-lists from the ios router
        # Get the remarks on access-lists from the ios router
        # alternate command 'sh run partition access-list' but has a lot of ordering issues
        # and incomplete ACLs are not viewed correctly
        _acl_data = connection.get("show ip access-list")
        _remarks_data = connection.get(
            "alias-get-acl-remarks",
        )
        if _remarks_data:
            remarks_config = []
            # add a tag so we can distinct between "show int" and "show run" output
            for rem in _remarks_data.split("\n"):
                rem = re.sub(r"^(ip )", "ip-remark ", rem)
                rem = re.sub(r"^(ipv6 )", "ipv6-remark ", rem)
                remarks_config.append(rem)
            _acl_data += "\n" + "\n".join(remarks_config)
        return _acl_data

    def sanitize_data(self, data):
        """removes matches or extra config info that is added on acl match"""
        re_data = ""
        for da in data.split("\n"):
            if "match" in da:
                mod_da = re.sub(r"\([^()]*\)", "", da)
                re_data += mod_da[:-1] + "\n"
            elif da.startswith("interface"):
                continue
            else:
                re_data += da + "\n"
        return re_data

    def populate_facts(self, connection, ansible_facts, data=None):
        """Populate the facts for Acls network resource

        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf

        :rtype: dictionary
        :returns: facts
        """
        facts = {}
        objs = []

        if not data:
            data = self.get_acl_data(connection)

        if data:
            data = self.sanitize_data(data)

        # parse native config using the Acls template
        acls_parser = AclsTemplate(
            lines=data.splitlines(), module=self._module
        )
        current = acls_parser.parse()

        temp_v4 = []
        temp_v6 = []

        if current.get("acls"):
            for k, v in iteritems(current.get("acls")):
                if v.get("afi") == "ipv4" and v.get("acl_type") in [
                    "standard",
                    "extended",
                ]:
                    del v["afi"]
                    temp_v4.append(v)
                elif v.get("afi") == "ipv6":
                    del v["afi"]
                    temp_v6.append(v)

            temp_v4 = sorted(temp_v4, key=lambda i: str(i["name"]))
            temp_v6 = sorted(temp_v6, key=lambda i: str(i["name"]))

            def process_protocol_options(each, acl_type):
                for each_ace in each.get("aces"):

                    if each_ace.get("source"):
                        if len(each_ace.get("source")) == 1 and each_ace.get(
                            "source",
                            {},
                        ).get("address"):
                            each_ace["source"]["host"] = each_ace[
                                "source"
                            ].pop("address")
                        if each_ace.get("source", {}).get("address"):
                            addr = each_ace.get("source", {}).get("address")
                            if addr[-1] == ",":
                                each_ace["source"]["address"] = addr[:-1]

                    if acl_type == "extended" and not each_ace.get(
                        "protocol", None
                    ):
                        each_ace["protocol"] = "ip"

                    if each_ace.get("protocol"):
                        each_ace.setdefault("protocol_options", {})
                        each_ace["protocol_options"][
                            "protocol"
                        ] = each_ace.pop("protocol")

                    for protocol_option in [
                        "protocol_number",
                        "icmp_message_code",
                        "icmp_message_type",
                    ]:
                        if each_ace.get(protocol_option):
                            each_ace["protocol_options"][
                                protocol_option
                            ] = each_ace.pop(protocol_option)

            def collect_remarks(aces):
                """makes remarks list per ace"""
                ace_entry = []
                rem = []
                for i in aces:
                    if i.get("remarks"):
                        rem.append(i.pop("remarks"))
                    else:
                        ace_entry.append(i)
                if rem:
                    ace_entry.append({"remarks": rem})
                return ace_entry

            for each in temp_v4:
                if each.get("aces"):
                    each["aces"] = collect_remarks(each.get("aces"))
                    process_protocol_options(
                        each, each.get("acl_type", "standard")
                    )

            for each in temp_v6:
                if each.get("aces"):
                    each["aces"] = collect_remarks(each.get("aces"))
                    process_protocol_options(
                        each, each.get("acl_type", "standard")
                    )

        objs = []
        if temp_v4:
            objs.append({"afi": "ipv4", "acls": temp_v4})
        if temp_v6:
            objs.append({"afi": "ipv6", "acls": temp_v6})

        facts = {}
        if objs:
            facts["acls"] = []
            params = utils.validate_config(
                self.argument_spec,
                {"config": objs},
            )
            for cfg in params["config"]:
                facts["acls"].append(utils.remove_empties(cfg))
        ansible_facts["ansible_network_resources"].update(facts)

        return ansible_facts
