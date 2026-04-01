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
import csv
import json
import logging
from lxml import etree
from . import shared
from .grok import Grok
from . import pixelcheck
from . import propertiescheck

__version__ = "0.1.0"

# Create parser
parser = argparse.ArgumentParser(description="JP2 Batch converter")


def parseCommandLine():
    """Parse command line"""
    # Add arguments
    parser.add_argument('dirIn',
                        action="store",
                        type=str,
                        help="input directory")
    parser.add_argument('dirOut',
                        action="store",
                        type=str,
                        help="output directory")
    parser.add_argument('--version', '-v',
                        action='version',
                        version=__version__)


    # Parse arguments
    args = parser.parse_args()

    return args


def readConfigFile(configFile):
    """read configuration file and return contents as dictionary"""

    configDict = {}

    # Read config file to dictionary
    try:
        with open(configFile, 'r', encoding='utf-8') as f:
            configDict = json.load(f)
    except:
        raise

    return configDict


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


def processFiles(listFiles, dirIn, dirOut, configDict, schema):
    """Process all files in list"""
    # TODO rewrite as a class

    # Start Grok class instance
    grok = Grok()
    grok.configDict = configDict
    grok.configure()
    grok.compressionProfile = "KB_MASTER_LOSSLESS_01/01/2015"
    #grok.compressionProfile = "KB_ACCESS_LOSSY_01/01/2015"

    # Summary file
    summaryFile = os.path.join(dirOut, "summary.csv")
    summaryHeadings = ["fileIn", "fileOut", "successGrok", "successPixelCheck", "successJpylyzerCheck", "failedJpylyzerChecks"]

    with open(summaryFile, 'w', newline='', encoding='utf-8') as fSum:
        # TODO read delimiter from configuration file
        writer = csv.writer(fSum, delimiter=";")
        writer.writerow(summaryHeadings)

    # Checksum file
    checksumFile = os.path.join(dirOut, "checksums.sha256")

    for fileIn in listFiles:
        successGrok = False
        successPixelCheck = False
        successJpylyzerCheck = False
        fileNameIn = os.path.basename(fileIn)
        filePathIn = os.path.dirname(fileIn)
        filePathInRel = os.path.relpath(filePathIn, start=dirIn)
        filePathOut = os.path.abspath(os.path.join(dirOut, filePathInRel))

        # Create filePathOut if it doesn't exist (including any missing parent dirs)
        if not os.path.isdir(filePathOut):
            os.makedirs(filePathOut)

        # Construct name for output file
        pre, ext = os.path.splitext(fileNameIn)
        fileNameOut = "{}.{}".format(pre, "jp2")

        fileOut = os.path.abspath(os.path.join(filePathOut, fileNameOut))

        logging.info("#############################")
        logging.info("Input image: {}".format(fileIn))
        logging.info("Output image: {}".format(fileOut))

        # Pass I/O to Grok instance and run the conversion
        grok.imageIn = fileIn
        grok.jp2Out = fileOut
        grok.compress()

        logging.info("grk_compress exit status: {}".format(grok.status))
        if grok.status == 0:
            successGrok = True
            logging.info("grok.compress completed successfully")
        elif grok.status != 0:
            logging.error("abnormal grk_compress exit status")
        if not grok.success:
            logging.error("grok.compress function resulted in an exception")

        # Check on pixel values
        sumPixelDifferences = pixelcheck.sumDifferences(fileIn, fileOut)
        if sumPixelDifferences == None:
             logging.error("pixel difference check failed with exception")
        if sumPixelDifferences == 0:
            logging.info("pixel values of input and output images are identical")
            successPixelCheck = True
        else:
            logging.error("pixel values of input and output images are not identical")
        logging.info("Sum of absolute pixel differences: {}".format(sumPixelDifferences))

        # Analyze JP2 with Jpylyzer and evaluate output against Schematron policy
        # TODO this now fails on xmlBox test because Grok doesn't support this (perhaps relax specs?)
        status, schTestsFailed, jpTestsFailed = propertiescheck.propertiesCheck(fileOut, schema)
        if status == "pass":
            successJpylyzerCheck = True
            logging.info("image conforms to Schematron rules")
        else:
            # Add failed tests to pipe-delimited string that is included in summary file
            schTestsFailedOut = []
            for schtest in schTestsFailed:
                schTestsFailedOut.append(schtest[0])

            schTestsFailedStr = '|'.join(schTestsFailedOut)
            logging.error("image does not conform to Schematron rules")

        # Calculate checksum (SHA-256)
        checksum = shared.generate_file_sha256(fileOut)

        # File reference, relative to output directory
        fileOutRel = os.path.relpath(fileOut, start=dirOut)

        # Construct checksum line, following https://superuser.com/a/1566139/681049
        checksumLine = "{}  {}\n".format(checksum, fileOutRel)

        # Write checksum line to file
        with open(checksumFile, 'a', newline='', encoding='utf-8') as fC:
            fC.write(checksumLine)

        # Write outcomes of QA checks to summary file
        with open(summaryFile, 'a', newline='', encoding='utf-8') as fSum:
            writer = csv.writer(fSum, delimiter=";")
            row = [fileIn, fileOut, successGrok, successPixelCheck, successJpylyzerCheck, schTestsFailedStr]
            writer.writerow(row)


def main():
    """Main function"""
    # TODO: split CLI stuff and configuration stuff into separate functions
    # Path to configuration dir (from https://stackoverflow.com/a/53222876/1209004
    # and https://stackoverflow.com/a/13184486/1209004).
    configPath = os.path.join(
    os.environ.get('LOCALAPPDATA') or
    os.environ.get('XDG_CONFIG_HOME') or
    os.path.join(os.environ['HOME'], '.config'),
    "jp2batchconverter")

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

    # Read config file
    configDict = readConfigFile(configFile)

    # TODO validate contents of config file for completeness

    # List of file extensions to process (case insensitive)
    # TODO perhaps allow user to override this using command-line option?
    extensions = configDict["inExtensions"]

    # Get input from command line
    args = parseCommandLine()
    dirIn = os.path.normpath(args.dirIn)
    dirOut = os.path.normpath(args.dirOut)

    # Check if files / directories exist
    shared.checkDirExists(dirIn)
    if not os.path.isdir(dirOut):
        try:
            os.makedirs(dirOut)
        except exception:
            msg = "creation of output directory {} failed".format(outDir)
            shared.errorExit(msg)

    # Check if outDir is writable
    if not os.access(dirOut, os.W_OK):
        msg = "directory {} is not writable".format(outDir)
        shared.errorExit(msg)

    # Set up logging
    logFile = os.path.join(dirOut, 'jp2batchconverter.log')
    logging.basicConfig(handlers=[logging.StreamHandler(sys.stdout),
                                  logging.FileHandler(logFile, 'a', 'utf-8')],
                        level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    # List of all files
    listFiles = getFilesFromTree(dirIn, extensions)

    # Start clock for statistics
    start = time.time()
    logging.info("jp2batchconverter started: {}".format(time.asctime()))

    ## TEST
    # TODO think about where/how to set this (in config file?)
    schema = os.path.join(configPath, "schemas", "kbMaster_2015.sch")
    ## TEST

    # Process all input files
    processFiles(listFiles, dirIn, dirOut, configDict, schema)

    # Timing output
    end = time.time()
    logging.info("jp2batchconverter ended: {}".format(time.asctime()))
    # Elapsed time (seconds)
    timeElapsed = end - start
    timeInMinutes = round((timeElapsed / 60), 2)
    logging.info("Elapsed time: {} minutes".format(timeInMinutes))



if __name__ == "__main__":
    main()
