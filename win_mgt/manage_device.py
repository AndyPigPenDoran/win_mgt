import sys
import argparse
import logging

import constants as c
import argument_defs
from utilities import CustomFormatter, get_password, show_inputs

# If pypsrp is not present, this import will fail
try:
    import transport_pypsrp as p
    HAS_PYPSRP = True
    IMPORT_ERROR = None
except ImportError as e:
    HAS_PYPSRP = False
    IMPORT_ERROR = "The pypsrp module could not be loaded. Error: %s" % str(e)


def main():
    """Main routine starting point"""
    logger.info("Starting")

    # If the password is not entered then ask for it
    password = get_password(args.user, args.pwd)

    # If the password is still empty then we cannot carry on
    if password is None or len(password) == 0:
        logger.error("No password was supplied for user: %s", args.user)
        return
    show_inputs(logger, args)

    
if __name__ == "__main__":
    # First process arguments
    parser = argparse.ArgumentParser()

    # Positional args
    argument_defs.args_positional(parser)

    # Credential arguments
    cred_parser = parser.add_argument_group("credentials settings")
    argument_defs.args_credentials(cred_parser)

    # Connection arguments
    connect_parser = parser.add_argument_group("connection settings")
    argument_defs.args_connect(connect_parser)

    # Optional arguments
    optional_parser = parser.add_argument_group("additional settings")
    argument_defs.args_optional(optional_parser)

    args = parser.parse_args()

    # Now set up logging
    logger = logging.Logger(__name__)
    logger.level = logging.DEBUG if args.debug else logging.INFO
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(CustomFormatter())
    logger.addHandler(h)

    if HAS_PYPSRP:
        main()
    else:
        logger.error(IMPORT_ERROR)
