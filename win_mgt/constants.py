
CHOICES_TASKS = {
    "shutdown": {
        "restart-now": {
            "command_type_raw": True,
            "command": "shutdown -r -t 0 -f",
            "has_options": False
        }
    },
    "services": {
        "list": {
            "command_type_raw": False,
            "command": "Get-Service",
            "has_options": False        
        },
        "restart": {
            "command_type_raw": False,
            "command": "Restart-Service",
            "has_options": True,
            "option_list": {
                "-Name": {
                    "type": str,
                    "required": True
                }
            }
        }
    },
    "filesystem": {}
}


# Connection options
PROTOCOL_HTTP, PROTOCOL_HTTPS = ("HTTP", "HTTPS")
CHOICES_PROTOCOLS = [PROTOCOL_HTTP, PROTOCOL_HTTPS]
DEFAULT_PROTOCOL = PROTOCOL_HTTP

DEFAULT_PORTS = {
    PROTOCOL_HTTP: 5985,
    PROTOCOL_HTTPS: 5986
}

MSG_ENCRYPTION_AUTO, MSG_ENCRYPTION_NEVER, MSG_ENCRYPTION_ALWAYS = ("auto", "never", "always")
CHOICES_MSG_ENCRYPTION = [
    MSG_ENCRYPTION_AUTO, 
    MSG_ENCRYPTION_NEVER, 
    MSG_ENCRYPTION_ALWAYS
]
DEFAULT_MSG_ENCRYPTION = MSG_ENCRYPTION_AUTO

PYPSRP_KERBEROS = "kerberos"
PYPSRP_BASIC = "basic"

DEFAULT_PYPSRP_ARGS = {
    "server": "", #The hostname or IP address of the host to connect to
    "max_envelope_size": 153600, #The maximum envelope size, in bytes, that can be sent to the server, default is 153600
    "operation_timeout": 20, # The operation timeout, in seconds, of each WSMan operation, default is 20. This should always be lower than read_timeout.
    "port": 5986, #The port to connect to, default is 5986 if ssl=True else 5985
    "username": "", #The username to connect with, required for all auths except certificate and optionally required for negotiate/kerberos
    #password: The password for username. Due to a bug on MacOS/Heimdal GSSAPI implementations, this will persist in the user's ccache when using Negotiate or Kerberos authentication, run kdestroy manually to remove this
    "ssl": True, #Whether to connect over https or https, default is True
    "path": "wsman", #The WinRM path to connect to, default is wsman
    "auth": "negotiate", #The authentication protocol to use, default is negotiate, choices are basic, certificate, negotiate, ntlm, kerberos, credssp
    "cert_validation": True, #Whether to validate the server's SSL certificate, default is True. Can be False to not validate or a path to a PEM file of trusted certificates
    "connection_timeout": 30, #The timeout for creating a HTTP connection, default is 30
    "read_timeout": 30, #The timeout for receiving a response from the server after a request has been made, default is 30
    "encryption": "auto", #Controls the encryption settings, default is auto, choices are auto, always, never. Set to always to always run message encryption even over HTTPS, never to never use message encryption even over HTTP
    "proxy": "", #The proxy URL used to connect to the remote host
    "no_proxy": False, #Whether to ignore any environment proxy variable and connect directly to the host, default is False
    "locale": "en-US", #The wsmv:Locale value to set on each WSMan request. This specifies the language in which the cleint wants response text to be translated, default is en-US
    "data_locale": "en-US", #The wsmv:DataLocale value to set on each WSMan request. This specifies the format in which numerical data is presented in the response text, default is the value of locale
    "reconnection_retries": 0, #Number of retries on a connection problem, default is 0
    "reconnection_backoff": 2.0, #Number of seconds to backoff in between reconnection attempts (first sleeps X, then sleeps 2X, 4X, 8*X, ...), default is 2.0
    "certificate_key_pem": "", #The path to the certificate key used in certificate authentication
    "certificate_pem": "", #The path to the certificate used in certificate authentication
    "credssp_auth_mechanism": "auto", #The sub-auth mechanism used in CredSSP, default is auto, choices are auto, ntlm, or kerberos
    "credssp_disable_tlsv1_2": False, #Whether to used CredSSP auth over the insecure TLSv1.0, default is False
    "credssp_minimum_version": 2, #The minimum CredSSP server version that the client will connect to, default is 2
    "negotiate_delegate": False, #Whether to negotiate the credential to the host, default is False. This is only valid if negotiate auth negotiated Kerberos or kerberos was explicitly set
    "negotiate_hostname_override": "", #The hostname used to calculate the host SPN when authenticating the host with Kerberos auth. This is only valid if negotiate auth negotiated Kerberos or kerberos was explicitly set
    "negotiate_send_cbt": True, #Whether to binding the channel binding token (HTTPS only) to the auth or ignore, default is True
    "negotiate_service": "HTTP" #Override the service part of the calculated SPN used when authenticating the server, default is WSMAN. This is only valid if negotiate auth negotiated Kerberos or kerberos was explicitly set
}

# Kerberos constants
KRB_KINIT_OK = 0
KRB_RETRY_CACHE = 1
KRB_FAIL = 2
