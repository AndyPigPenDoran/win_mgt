import socket
import re

def _is_ipv6(host):
    """IPv6 address??"""
    return len(host.split(":")) == 8

def _is_ipv4(host):
    """IPv4 address??"""
    pattern = r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
    return re.match(pattern, host)

class Network:
    def __init__(self, logger):
        self.logger = logger
        self.host_info = self._set_dict()

    def _set_dict(self):
        """Default values for dictionary"""
        return {
            "host": "",
            "fqdn": "",
            "ip": "",
            "is_resolved": False,
            "is_ipv6": False
        }
    

    def _is_ip(self, host):
        """See if this is IP - and whether it is IPv6"""
        # Test for IPv6 first
        if _is_ipv6(host):
            self.host_info["ip"] = host
            self.host_info["is_ipv6"] = True
            return
        
        # Now test for IPv4
        if _is_ipv4(host):
            self.host_info["ip"] = host
            self.host_info["is_ipv6"] = False
            return
        
        # Must be a host name
        self.host_info["host"] = host
        return
    

    def resolve_host(self, host):
        """Try to resolve a host name/ip to get host, fqdn and IP"""
        try:
            host_info = socket.gethostbyaddr(host)
        except socket.herror:
            self.logger.debug("network.resolve_host: Failed to resolve host from: %s", host)
            # Return what information we have
            self._is_ip(host)
            # Set the host to be the input
            self.host_info["host"] = host
            return self.host_info
        
        self.host_info["host"] = host_info[0]
        self.host_info["fqdn"] = host_info[1][0]
        self.host_info["ip"] = host_info[2][0]
        self.host_info["is_ipv6"] = _is_ipv6(self.host_info["ip"])
        self.host_info["is_resolved"] = True

        return self.host_info
    
    def ping_host(self, port):
        """Attempt to ping a device"""

        # Should the ping be IPv6 or IPv4
        family = socket.AF_INET6 if self.host_info["is_ipv6"] else socket.AF_INET
        sock = socket.socket(family)
        r = None

        try:
            r = sock.connect_ex((self.host_info["ip"], port))
        except socket.gaierror as e:
            self.logger.error(
                "Error in ping test: %s", str(e)
            )
            self.logger.debug("Host info: %s", self.host_info)
        finally:
            sock.close()

        if r is not None and int(r) == 0:
            return True
        else:
            self.logger.debug(
                "network.ping_test: Ping failed with code: %s", r
            )
            return False
        
        return True
