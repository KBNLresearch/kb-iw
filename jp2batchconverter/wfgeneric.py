#! /usr/bin/env python3

"""
Module with generic workflow
"""

import os
import csv
import hashlib
import logging
from . import shared
from .grok import Grok
from . import pixelcheck
from . import propertiescheck

def workflowGeneric(dirIn, dirOut, configPath, configDict):
    """Process all files in list"""

    # List of file extensions to process (case insensitive)
    extensions = configDict["inExtensions"]

    # Output delimiter
    outDelimiter = configDict["outDelimiter"]

    # List of all input files
    listFiles = shared.getFilesFromTree(dirIn, extensions)

    # Schematron schema for properties check
    schema = os.path.join(configPath, "schemas", "kbMaster_2015.sch")

    # Start Grok class instance
    grok = Grok()
    grok.configDict = configDict
    grok.configure()
    grok.compressionProfile = "KB_MASTER_LOSSLESS_01/01/2015"
    #grok.compressionProfile = "KB_ACCESS_LOSSY_01/01/2015"

    # Summary file
    summaryFile = os.path.join(dirOut, "summary.csv")

    # Checksum file
    checksumFile = os.path.join(dirOut, "checksums.sha256")

    # Remove any previous summary / checksum file instances
    if os.path.isfile(summaryFile):
        os.remove(summaryFile)
    if os.path.isfile(checksumFile):
        os.remove(checksumFile)

    # Write header to summary file
    summaryHeadings = ["fileIn", "fileOut", "successGrok", "successPixelCheck",
                       "successJpylyzerCheck", "failedJpylyzerChecks"]

    with open(summaryFile, 'w', newline='', encoding='utf-8') as fSum:
        writer = csv.writer(fSum, delimiter=outDelimiter)
        writer.writerow(summaryHeadings)

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
        ssDiff = pixelcheck.sumSqDiff(fileIn, fileOut)

        if ssDiff == None:
             logging.error("pixel difference check failed with exception")
        if ssDiff == 0:
            logging.info("pixel values of input and output images are identical")
            successPixelCheck = True
        else:
            logging.error("pixel values of input and output images are not identical")
        logging.info("Sum of squared pixel differences: {}".format(ssDiff))

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
            writer = csv.writer(fSum, delimiter=outDelimiter)
            row = [fileIn, fileOut, successGrok, successPixelCheck, successJpylyzerCheck, schTestsFailedStr]
            writer.writerow(row)
