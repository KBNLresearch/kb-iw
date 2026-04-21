#! /usr/bin/env python3

"""JP2 Batch converter

Johan van der Knijff

Copyright 2026, KB/National Library of the Netherlands

"""

import sys
import os
import io
import shutil
import time
import argparse
import json
import logging
from . import shared
from . import wfgeneric

__version__ = "0.1.0"

# Create parser
parser = argparse.ArgumentParser(description="JP2 Batch converter")


def parseCommandLine():
    """Parse command line"""
    # Add arguments
    parser.add_argument("dirIn",
                        action="store",
                        type=str,
                        help="input directory")
    parser.add_argument("dirOut",
                        action="store",
                        type=str,
                        help="output directory")
    parser.add_argument("workflow",
                        action="store",
                        type=str,
                        help="workflow (generic, metamorfoze, beeldstudio)")
    parser.add_argument("--version", "-v",
                        action="version",
                        version=__version__)

    # Parse arguments
    args = parser.parse_args()

    return args


def configure(configPath):

    """
    Set up configuration dir if it doesn't exist already, and read configuration
    """

    # Locate package directory
    packageDir = os.path.dirname(os.path.abspath(__file__))

    # Config locations in installed package and system config folder
    configDirPackage = os.path.join(packageDir, "conf")

    # Check if package conf dir exists
    shared.checkDirExists(configDirPackage)

    # Copy contents of package config dir to system config dir
    if not os.path.isdir(configPath):
        shutil.copytree(configDirPackage, configPath, dirs_exist_ok = True)

    configFile = os.path.join(configPath, "config.json")
    if not os.path.isfile(configFile):
        msg = "configuration file ({}) is missing".format(configFile)
        shared.errorExit(msg)

    # Read config file to dictionary
    configDict = {}

    try:
        with open(configFile, 'r', encoding='utf-8') as f:
            configDict = json.load(f)
    except:
        raise

    # Some light validation of config file contents
    if not "grokDir" in configDict:
        msg = "\"grokDir\" entry missing configuration file"
        shared.errorExit(msg)
    if not "compressionProfiles" in configDict:
        msg = "\"compressionProfiles\" entry missing in configuration file"
        shared.errorExit(msg)

    for compressionProfile in configDict["compressionProfiles"]:
        print(type(compressionProfile["name"]))
        if not "name" in compressionProfile:
            msg = "\"name\" entry missing in configuration file"
            shared.errorExit(msg)
        if type(compressionProfile["name"]) != str:
            msg = "\"name\" value is not a string"
            shared.errorExit(msg)
        if not "params" in compressionProfile:
            msg = "\"params\" entry missing in configuration file"
            shared.errorExit(msg)
        if type(compressionProfile["params"]) != list:
            msg = "\"params\" value is not a list"
            shared.errorExit(msg)

    return configDict


def main():
    """Main function"""

    # Path to configuration dir (from https://stackoverflow.com/a/53222876/1209004
    # and https://stackoverflow.com/a/13184486/1209004).
    configPath = os.path.join(
    os.environ.get('LOCALAPPDATA') or
    os.environ.get('XDG_CONFIG_HOME') or
    os.path.join(os.environ['HOME'], '.config'),
    "jp2batchconverter")

    # Get configuration, and set up local configuration if it doesn't exist
    configDict = configure(configPath)

    # Get input from command line
    args = parseCommandLine()
    dirIn = os.path.normpath(args.dirIn)
    dirOut = os.path.normpath(args.dirOut)
    workflow = os.path.normpath(args.workflow)

    # Check if files / directories exist
    shared.checkDirExists(dirIn)

    # Check if workflow value is valid
    workflowsAllowed = ["generic", "metamorfoze", "beeldstudio"]
    if workflow not in workflowsAllowed:
        msg = "workflow \"{}\" does not exist. Expected one of these values:".format(workflow)
        for wf in workflowsAllowed:
            msg += "\n  - {}".format(wf)
        shared.errorExit(msg)

    # Create dirOut if it doesn't exist already
    if not os.path.isdir(dirOut):
        try:
            os.makedirs(dirOut)
        except exception:
            msg = "creation of output directory {} failed".format(outDir)
            shared.errorExit(msg)

    # Set up logging
    logFile = os.path.join(dirOut, 'jp2batchconverter.log')
    logging.basicConfig(handlers=[logging.StreamHandler(sys.stdout),
                                  logging.FileHandler(logFile, 'a', 'utf-8')],
                                  level=logging.INFO,
                                  format='%(asctime)s - %(levelname)s - %(message)s')

    # Start clock for statistics
    start = time.time()
    logging.info("jp2batchconverter started: {}".format(time.asctime()))
    logging.info("starting workflow \"{}\"".format(workflow))

    # Run selected workflow
    if workflow == "generic":
        wfgeneric.workflowGeneric(dirIn, dirOut, configPath, configDict)

    # Timing output
    end = time.time()
    logging.info("jp2batchconverter ended: {}".format(time.asctime()))
    # Elapsed time (seconds)
    timeElapsed = end - start
    timeInMinutes = round((timeElapsed / 60), 2)
    logging.info("Elapsed time: {} minutes".format(timeInMinutes))


if __name__ == "__main__":
    main()
