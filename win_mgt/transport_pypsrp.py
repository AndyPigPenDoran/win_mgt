
from pypsrp import exceptions as pypsrp_exceptions
from pypsrp.client import Client
from pypsrp.powershell import PowerShell, RunspacePool
from pypsrp.wsman import WSMan
from spnego.exceptions import SpnegoError, BadMechanismError, CredentialsExpiredError

import constants as c
from utilities import pad_string
from network import Network

class Transport:
    def __init__(self, logger, args, password):
        self.logger = logger
        self.network = Network(self.logger)
        self.password = password
        self.kwargs = c.DEFAULT_PYPSRP_ARGS
        self.connected = False
        self.principal = None
        self.domain = None
        self.ping = args.ping
        self.ok_continue = True
        self._process_args(args)

    def _process_args(self, args):
        """Update kwargs with values in args (ie inputs)"""
        args_dict = {}

        for arg in vars(args):
            if arg in self.kwargs:
                self.kwargs[arg] = getattr(args, arg)

    def _prepare_user(self):
        """Configure the user - is it local or Active Directory"""
        _user = self.kwargs["username"]

        if _user.find("@") != -1 or _user.find("\\") != -1:
            # Must be Active Directory
            if _user.find("@") != -1:
                # user@domain
                _principal, _domain = _user.rsplit("@")
            else:
                # domain\user
                _domain, _principal = _user.rsplit("\\")

            # Set the domaimn is upper
            self.principal = _principal
            self.domain = _domain.upper()
            self.kwargs["auth"] = c.PYPSRP_KERBEROS
        else:
            # Local - can't use message encryption, so override any choice mad
            self.kwargs["auth"] = c.PYPSRP_BASIC
            self.kwargs["encryption"] = c.MSG_ENCRYPTION_NEVER
            
    def _prepare_host(self):
        """Try and get the host name plus IP etc"""
        host_info = self.network.resolve_host(self.kwargs["server"])
        
        if host_info["is_resolved"]:
            self.kwargs["server"] = host_info["fqdn"] if len(host_info["fqdn"]) > 0 else \
                host_info["host"]
        else:
            if self.kwargs["auth"] == c.PYPSRP_KERBEROS:
                self.logger.warning(
                    "transport_pypsrp._prepare_host: The IP address could not be resolved, this " 
                    "is a requirement for Active Directory connections. An attempr will be made " 
                    "to connect, but is likely to fail."
                )

        if self.ping:
            self.ok_continue = self.network.ping_host(self.kwargs["port"])

        if not self.ok_continue:
            self.logger.error(
                "transport_pypsrp._prepare_host: Unable to ping server %s on port %s, quitting",
                self.kwargs["server"], self.kwargs["port"]
            )
            

    def _prepare_port(self):
        """If no port is set then pick one based on the protocol"""
        if self.kwargs["port"] is not None:
            return
        
        self.kwargs["port"] = c.DEFAULT_PORTS["HTTPS"] if self.kwargs["ssl"] else \
            c.DEFAULT_PORTS["HTTP"]


    def _prepare_connection(self):
        """Check some of the inputs"""
        self._prepare_user()
        self._prepare_port()
        self._prepare_host()


    def connect(self):
        """Establish a connection to the target"""

        # Fixup things like server lookup, user is local or Active Directory etc
        self._prepare_connection()

        if not self.ok_continue:
            return

        _pad_len = 30
        _msg = "Parameters for connection\n\n"

        for k, v in self.kwargs.items():
            _msg += "  %s: %s\n" % (pad_string(k, _pad_len), v)

        self.logger.debug(_msg)
