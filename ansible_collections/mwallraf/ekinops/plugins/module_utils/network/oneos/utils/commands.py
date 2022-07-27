class OneosCommandV5:

    # map an alias to a command
    COMMANDMAP = {
        "alias-get-hostname": "show running-config | i hostname",
        "alias-get-interface-acl": "show running-config"
        " | include (interface|access)",
    }

    # commands used to parse Hardware facts
    COMMANDS_HARDWARE_FACTS = [
        "show system status",
        "show system hardware",
        "show memory",
        "cat /BSA/bsaBoot.inf",
        "ls /BSA/binaries",
        "ls /BSA/config",
        "show device status flash",
        "show device status ram",
    ]


class OneosCommandV6:

    # map an alias to a command
    COMMANDMAP = {
        "alias-get-hostname": "show running-config hostname",
        "alias-get-interface-acl": "show running-config interface"
        ' | i "(interface|access-group)"',
    }

    # commands used to parse Hardware facts
    COMMANDS_HARDWARE_FACTS = [
        "show system status",
        "show system hardware",
        "show memory details",
        "ls -l /BSA/binaries",
        "ls -l /BSA/config",
        "show software-image",
    ]


class OneosCommand:
    """Base class for OneOs specific commands

    The base class will determine which child class to generate:
        OneosCommandV5  (for oneos 5)
        OneosCommandV6  (for oneos 6)

    The purpose of this class is to return the optimal command
    for the given OneOs version.

    Example:
      "alias-get-hostname"
         version 5 = show running-config | include hostname
         version 6 = show running-config hostname

    Usage:
        >>> from ansible_collections.mwallraf.ekinops.plugins.module_utils.\
            network.oneos.utils.commands import OneosCommand
        >>> a = OneosCommand(5)
        >>> a.get("show run")
        'show run'
        >>> a.get("alias-get-hostname")
        'show running-config | i hostname'
        >>>
        >>> a = OneosCommand(6)
        >>> a.get("alias-get-hostname")
        'show running-config hostname'
        >>>
    """

    __SUPPORTED_VERSIONS__ = ["5", "6"]

    def __init__(self, version=None) -> None:
        if str(version) not in self.__SUPPORTED_VERSIONS__:
            raise Exception("unsupported oneos version")

        self.version = str(version)
        self.commands = self._get_commands()
        self.facts_hardware_commands = self._get_facts_hardware_commands()

    def get(self, cmd):
        """If a specific command (or alias) exists for the
        OS version then return it, otherwise return the
        original command
        """
        oneos_cmd = self.commands.get(cmd, None)
        return oneos_cmd

    def __repr__(self) -> str:
        return f"<OneosCommandV{self.version}>"

    def __str__(self) -> str:
        return f"<OneosCommandV{self.version}>"

    def _get_commands(self):
        _obj = eval("OneosCommandV" + self.version)
        return _obj.COMMANDMAP

    def _get_facts_hardware_commands(self):
        _obj = eval("OneosCommandV" + self.version)
        return _obj.COMMANDS_HARDWARE_FACTS
