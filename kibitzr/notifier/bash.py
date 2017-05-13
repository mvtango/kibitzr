from ..bash import execute_bash
import logging

logger = logging.getLogger(__name__)

class BashNotify(object):

    def __init__(self, value, conf):
        self.code = value
        self.conf = conf

    def __call__(self, report):
        rv=execute_bash(self.code, report)
        if rv[0] :
            logger.info("Notified {} via bash".format(self.conf.get("name","")))


def notify_factory(conf, value):
    return(BashNotify(value,conf))

