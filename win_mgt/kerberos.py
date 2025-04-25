import subprocess
import sys
import os

import constants as c

IS_PY3 = int(sys.version[0]) > 2

class Kerberos:
    def __init__(self, logger, args):
        self.logger = logger
        self.principal = ""
        self.domain = ""
        self.timeout = args.kinit_timeout
        self.force_cache = args.force_cache
        self.cache = ""


    def _kinit(self, password, use_cache=False):
        """Run the kinit command"""
        user_string = "%s%s" % (self.principal, self.domain)

        try:
            if use_cache:
                self.logger.debug("running kinit with cache: %s", self.cache)
                ph = subprocess.Popen(
                    ["kinit", "-c", self.cache, user_string],
                    stdout = subprocess.PIPE,
                    stderr = subprocess.PIPE,
                    stdin = subprocess.PIPE
                )
            else:
                self.logger.debug("running kinit without a cache")
                ph = subprocess.Popen(
                    ["kinit", user_string],
                    stdout = subprocess.PIPE,
                    stderr = subprocess.PIPE,
                    stdin = subprocess.PIPE
                )

            self.logger.debug("Sending password")

            if IS_PY3:
                _stdout, _stderr = ph.communicate(
                    bytes(password, "utf-8"),
                    timeout=self.timeout
                )
            else:
                _stdout, _stderr = ph.communicate(password)

            if use_cache:
                os.environ["KRB5CCNAME"] = self.cache
            else:
                os.environ["KRB5CCNAME"] = ""

            return c.KRB_KINIT_OK
        except subprocess.TimeoutExpired:
            self.logger.error(
                "Reached maimum timeout (%s seconds) waiting for a response from the Domain " \
                "controller for %s", self.timeout, self.domain
            )
            return c.KRB_FAIL
        except Exception as e:
            err_type = type(e)
            err_str = str(e)
            self.logger.warning(
                "Error %s with kinit: %s", err_type, err_str
            )
            return c.KRB_RETRY_CACHE
                

    def get_ticket(self, principal, domain, password):
        """Get a ticket"""
        self.principal = principal
        self.domain = domain.upper()
        self.cache = "/tmp/krb5_%s_%s" % (self.domain, self.principal)
        err = self._kinit(password, self.force_cache)

        if err == c.KRB_KINIT_OK:
            return True
        
        if err == c.KRB_RETRY_CACHE:
            err = self._kinit(password, True)

            return err == c.KRB_KINIT_OK
        
        return False