#! /usr/bin/env python3

"""
Module with shared functions
"""

import sys
import os
import hashlib

def errorExit(msg):
    """Write error to stderr and exit"""
    msgString = "ERROR: {}\n".format(msg)
    sys.stderr.write(msgString)
    sys.exit()


def checkFileExists(fileIn):
    """Check if file exists and exit if not"""
    if not os.path.isfile(fileIn):
        msg = "file {} does not exist".format(fileIn)
        errorExit(msg)


def checkDirExists(pathIn):
    """Check if directory exists and exit if not"""
    if not os.path.isdir(pathIn):
        msg = "directory {} does not exist".format(pathIn)
        errorExit(msg)


def generate_file_sha256(fileIn):
    """Generate sha256 hash of file"""

    # fileIn is read in chunks to ensure it will work with (very) large files as well
    # Adapted from: http://stackoverflow.com/a/1131255/1209004

    blocksize = 2**20
    m = hashlib.sha256()
    with open(fileIn, "rb") as f:
        while True:
            buf = f.read(blocksize)
            if not buf:
                break
            m.update(buf)
    return m.hexdigest()
