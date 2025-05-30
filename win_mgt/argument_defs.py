import constants as c
import json

def args_positional(parser):
    """Positional arguments"""
    parser.add_argument("server", help="Windows server to manage", type=str)
    parser.add_argument(
        "task", help="task to perform", type=str.lower, choices=c.CHOICES_TASKS.keys()
    )
    parser.add_argument(
        "option", help="specific command for task", type=str.lower,
    )

def args_credentials(parser):
    """Arguments related to credentials"""
    parser.add_argument("-user", help="username", type=str, required=True, dest="username")
    parser.add_argument("-pwd", help="password", type=str)

def args_connect(parser):
    """Connection specific arguments"""
    parser.add_argument(
        "-protocol", help="protocol to use", type=str.upper,choices=c.CHOICES_PROTOCOLS,
        default=c.DEFAULT_PROTOCOL
    )
    parser.add_argument("-port", help="port", type=int)
    parser.add_argument(
        "--msg-encryption", help="message encryption", type=str.lower, 
        choices=c.CHOICES_MSG_ENCRYPTION, default=c.DEFAULT_MSG_ENCRYPTION,
        dest="encryption"
    )
    parser.add_argument(
        "-v", "--cert-validate", help="certificate validation", action="store_true",
        dest="cert_validation"
    )
    parser.add_argument(
        "--operation-timeout", help="operation timeout", type=int, 
        default=c.DEFAULT_PYPSRP_ARGS["operation_timeout"]
    )
    parser.add_argument(
        "--read-timeout", help="read timeout", type=int,
        default=c.DEFAULT_PYPSRP_ARGS["read_timeout"]
    )
    parser.add_argument(
        "--connection-timeout", help="connection timeout", type=int,
        default=c.DEFAULT_PYPSRP_ARGS["connection_timeout"]
    )

def args_command(parser):
    """Options relating to the command"""
    parser.add_argument(
        "--task-options", help="task specific options", type=json.loads
    )

def args_kerberos(parser):
    """Kerberos related"""
    parser.add_argument("--kinit-timeout", help="kinit timeout", type=int, default=10)
    parser.add_argument(
        "--force-cache", help="force the use of a cache file for kerberos ticket", 
        action="store_true"
    )

def args_optional(parser):
    """Arguments that are optional"""
    parser.add_argument("-n", help="do not ping target", action="store_false", dest="ping")
    parser.add_argument("-d", help="enable debug logging", action="store_true", dest="debug")
