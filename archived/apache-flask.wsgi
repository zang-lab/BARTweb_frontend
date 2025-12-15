#! /usr/bin/python3
# feed our front end to apache to run
import sys
sys.path.append("/BARTweb")  # docker path

from app import app as application
