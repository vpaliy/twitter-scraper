# coding: utf-8
from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

import logging
import coloredlogs
import agents

__author__ = "Vasyl Paliy"
__version__ = '0.1'
__license___ = "MIT"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
coloredlogs.install(level='INFO', logger=logger)
coloredlogs.install(fmt='%(asctime)s | %(message)s')

ua_provider = agents.UserAgentProvider()
