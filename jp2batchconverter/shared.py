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


def getFilesFromTree(rootDir, extensions):
    """Walk down whole directory tree (including all subdirectories) and
    return list of files whose extensions match extensions list
    NOTE: directory names are disabled here!!
    implementation is case insensitive (all search items converted to
    upper case internally!
    """

    # Convert extensions to uppercase
    extensions = [extension.upper() for extension in extensions]
    filesList = []

    for dirname, dirnames, filenames in os.walk(rootDir):
        # Suppress directory names
        for subdirname in dirnames:
            thisDirectory = os.path.join(dirname, subdirname)

        for filename in filenames:
            if filename.startswith("._"):
                # Ignore AppleDouble resource fork files (identified here by name)
                pass
            else:
                thisFile = os.path.join(dirname, filename)
                thisExtension = os.path.splitext(thisFile)[1]
                thisExtension = thisExtension.upper().strip('.')
                if extensions[0].strip() == '*' or thisExtension in extensions:
                    filesList.append(os.path.abspath(thisFile))
    return filesList
