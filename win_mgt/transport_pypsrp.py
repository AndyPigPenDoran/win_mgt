
import os

from pypsrp import exceptions as pypsrp_exceptions
from pypsrp.client import Client
from pypsrp.powershell import PowerShell, RunspacePool
from pypsrp.wsman import WSMan
from pypsrp.exceptions import AuthenticationError
from spnego.exceptions import SpnegoError, BadMechanismError, CredentialsExpiredError

import constants as c
from utilities import pad_string
from network import Network
from kerberos import Kerberos

class Transport:
    def __init__(self, logger, args, password):
        self.logger = logger
        self.network = Network(self.logger)
        self.kerberos = Kerberos(self.logger, args)
        self.password = password
        self.kwargs = c.DEFAULT_PYPSRP_ARGS
        self.connected = False
        self.principal = None
        self.domain = None
        self.ping = args.ping
        self.wsman = None
        self.runspacepool = None
        self.client = None
        self.ok_continue = True
        self.command = ""
        self.is_raw = False
        self.result_dict = self._set_result_dict()
        self._process_args(args)

    def _set_result_dict(self):
        """Use a dictionary for the results"""
        return {
            "is_raw": False,
            "is_error": False,
            "raw_result": "",
            "stdout": "",
            "stderr": "",
            "raw_result": ""
        }

    def _process_args(self, args):
        """Update kwargs with values in args (ie inputs)"""
        args_dict = {}

        for arg in vars(args):
            if arg in self.kwargs:
                self.kwargs[arg] = getattr(args, arg)
            elif arg == "protocol":
                self._prepare_ssl(getattr(args, arg))

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
            # Make sure user is in correct format with uppercase domain
            self.kwargs["username"] = "%s@%s" % (self.principal, self.domain)
        else:
            # Local - can't use message encryption, so override any choice mad
            self.kwargs["auth"] = c.PYPSRP_BASIC
            self.kwargs["encryption"] = c.MSG_ENCRYPTION_NEVER
            self.kwargs["password"] = self.password
            
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

    def _prepare_ssl(self, protocol):
        """Input is HTTP or HTTPS for protocol, translates to False/True for ssl"""
        self.kwargs["ssl"] = True if protocol == c.PROTOCOL_HTTPS else False


    def _set_timeouts(self):
        """Since the timeouts are user changeable, make sure they are valid"""
    
        operation_timeout = self.kwargs["operation_timeout"] \
            if 10 < self.kwargs["operation_timeout"] < 180 else 20
        connection_timeout = self.kwargs["connection_timeout"] \
            if 10 < self.kwargs["connection_timeout"] < 60 else 30
        read_timeout = self.kwargs["read_timeout"] \
            if 10 < self.kwargs["read_timeout"] < 60 else 30
    
        # operation timeout needs to be less than read timeout
        if operation_timeout < read_timeout:
            operation_timeout = read_timeout -2

        self.kwargs["operation_timeout"] = operation_timeout
        self.kwargs["connection_timeout"]= connection_timeout
        self.kwargs["read_timeout"] = read_timeout


    def _prepare_connection(self):
        """Check some of the inputs"""
        self._prepare_user()
        self._prepare_port()
        self._prepare_host()
        self._set_timeouts()

        if self.ok_continue and self.kwargs["auth"] == c.PYPSRP_KERBEROS:
            # Get a ticket
            self.ok_continue = self.kerberos.get_ticket(self.principal, self.domain, self.password)
        

    def _connect_pool(self):
        """Create a RunspacePool connection (PowerShell only)"""
        self.logger.info("Connecting for PowerShell execution")
        try:
            self.wsman = WSMan(**self.kwargs)
            self.runspacepool = RunspacePool(self.wsman)
            self.runspacepool.open()
            self.connected = True
        except (CredentialsExpiredError, BadMechanismError, SpnegoError) as e:
            self.logger.error("transport_pypsrp._connect_pool: Connection error: %s", str(e))
        except AuthenticationError as e:
            self.logger.error(
                "Unable to authenticate, check the user %s exists on the target. Error: %s",
                self.kwargs["username"], str(e)
            )
        except Exception as e:
            type_err = type(e)
            str_err = str(e)
            self.logger.error(
                "transport_pypsrp._connect_pool: Error %s trying to connect to server: %s", 
                type_err, str_err
            )

    def _connect_nonpool(self):
        """Used for DOS commands"""
        self.logger.info("Connecting for non-PowerShell execution")
        # This does not actually connect, just sets up Client to be used
        self.client = Client(**self.kwargs)
        self.connected = True


    def _run_pool(self):
        """Run command in RunspacePool"""
        try:
            ps = PowerShell(self.runspacepool)
            ps.add_cmdlet("Invoke-Expression").add_parameter("Command", self.command)
            ps.add_cmdlet("Out-String").add_parameter("Stream")
            ps.invoke()

            # Let the "read" function determine if there was an issue
            self.result_dict["ps_result"] = "\n".join(ps.output), ps.streams, ps.had_errors
            self.result_dict["is_error"] = False
        except Exception as e:
            err_type = type(e)
            err_str = str(e)
            err_msg = "Error %s running command: %s" % err_type, err_str
            self.result_dict["is_error"] = True
            self.result_dict["stderr"] = err_msg
            
    def _run_nonpool(self):
        """Use Client"""
        # This is where the connection is made for Client so assume no connection
        self.connected = False

        try:
            self.result_dict["raw_result"] = self.client.execute_cmd(self.command)
            self.connected = True
        except (CredentialsExpiredError, BadMechanismError, SpnegoError) as e:
            self.logger.error("transport_pypsrp._run_nonpool: Connection error: %s", str(e))
        except AuthenticationError as e:
            self.logger.error(
                "Unable to authenticate, check the user %s exists on the target. Error: %s",
                self.kwargs["username"], str(e)
            )            
        except Exception as e:
            type_err = type(e)
            str_err = str(e)
            self.logger.error(
                "transport_pypsrp._run_nonpool: Error %s trying to connect to server: %s", 
                type_err, str_err
            )

    def _read_pool(self):
        """Read result of runnibng in RunspacePool"""
        self.result_dict["stdout"] = self.result_dict["ps_result"][0]
        self.result_dict["is_error"] = self.result_dict["ps_result"][2]

        if self.result_dict["is_error"]:
            self.result_dict["stderr"] = self.result_dict["ps_result"][1].error[0]


    def _read_nonpool(self):
        """Read raw command result"""
        self.result_dict["stdout"] = self.result_dict["raw_result"][0]
        self.result_dict["is_error"] = self.result_dict["raw_result"][2]

        if self.result_dict["is_error"]:
            self.result_dict["stderr"] = self.result_dict["raw_result"][1].error[0]


    def connect(self, is_raw=False):
        """Establish a connection to the target"""

        # Fixup things like server lookup, user is local or Active Directory etc
        self._prepare_connection()

        if not self.ok_continue:
            return

        self.is_raw = is_raw
        _pad_len = 30
        _msg = "Parameters for connection\n\n"

        for k, v in self.kwargs.items():
            if k == "password":
                v = "**********"

            _msg += "  %s: %s\n" % (pad_string(k, _pad_len), v)

        if self.kwargs["auth"] == c.PYPSRP_KERBEROS:
            cache_name = os.getenv("KRB5CCNAME", "")
            if len(cache_name) > 0:
                _msg += "  %s: %s\n" % (pad_string("krb5 cache", _pad_len), cache_name)
            else:
                _msg += "  %s: %s\n" % (pad_string("krb5 cache", _pad_len), "Not used")

        self.logger.debug(_msg)
        if self.is_raw:
            self._connect_nonpool()
        else:
            self._connect_pool()

    def run_command(self, command):
        """Run a command"""
        # We could run multiple commands, so clear things up first
        self.result_dict = self._set_result_dict()
        self.command = command
        self.result_dict["is_raw"] = self.is_raw

        if self.is_raw:
            self._run_nonpool()
        else:
            self._run_pool()

        return not self.result_dict["is_error"]
    
    def get_results(self):
        """Get the results from running the command"""
        if self.is_raw:
            self._read_nonpool()
        else:
            self._read_pool()

        return not self.result_dict["is_error"]
    
    def disconnect(self):
        """Close connections"""

        if self.runspacepool:
            self.runspacepool = None
        if self.client:
            self.client = None
