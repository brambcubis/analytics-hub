# -*- coding: utf-8 -*-
"""
Created on Fri Feb 22 2019

@author: Bramb
"""

# Include packages
from oauthlib import oauth2
# import requests-oauthlib # Currently not working
import logging
import sys

# Enable logging
log = logging.getLogger('oauthlib')
log.addHandler(logging.StreamHandler(sys.stdout))
log.setLevel(logging.DEBUG)

# Start dev


if __name__ == '__main__':
    help(oauth2)
