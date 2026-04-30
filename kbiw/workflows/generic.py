#! /usr/bin/env python3

"""
Module with generic workflow
"""

import os
import csv
import hashlib
import logging
from .. import shared
from .. import grok
from .. import pixelcheck
from .. import propertiescheck

def workflow(dirIn, dirOut, configPath, configDict):
    """Generic workflow: process all """

    # List of file extensions to process (case insensitive)
    extensions = ["tif", "tiff"]

    # Schematron schema for properties check
    schema = os.path.join(configPath, "schemas", "kbMaster_2015.sch")

    # Output delimiter
    outDelimiter = ";"

    # Compression profile
    compressionProfile = "KB_MASTER_LOSSLESS_01/01/2015"
    #compressionProfile = "KB_ACCESS_LOSSY_01/01/2015"

    # List of all input files
    listFiles = shared.getFilesFromTree(dirIn, extensions)

    # Start Grok class instance
    myGrok = grok.Grok()
    myGrok.configDict = configDict
    myGrok.configure()
    myGrok.compressionProfile = compressionProfile

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
        schTestsFailedStr = ""
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
        myGrok.imageIn = fileIn
        myGrok.jp2Out = fileOut

        myGrok.compress()
        logging.info("grk_compress exit status: {}".format(myGrok.status))
        if myGrok.status == 0:
            successGrok = True
            logging.info("grok.compress completed successfully")
        elif myGrok.status != 0:
            logging.error("abnormal grk_compress exit status")
        if not myGrok.success:
            logging.error("grok.compress function resulted in an exception")

        logging.info("grk_compress stdout: {}".format(myGrok.out))
        logging.info("grk_compress stderr: {}".format(myGrok.errors))


        ## TEST
        logging.info("successGrok: {}".format(successGrok))
        ## TEST

        if successGrok:

            ## TEST
            logging.info("entering qua block")
            ## TEST

            try:
                # Check on pixel values
                ssDiff = pixelcheck.sumSqDiff(fileIn, fileOut)

                ## TEST
                logging.info("ssDiff: {}".format(ssDiff))
                ## TEST


                if ssDiff == None:
                    logging.error("pixel difference check failed with exception")
                if ssDiff == 0:
                    logging.info("pixel values of input and output images are identical")
                    successPixelCheck = True
                else:
                    logging.error("pixel values of input and output images are not identical")
                logging.info("Sum of squared pixel differences: {}".format(ssDiff))

            except Exception:
                logging.error("pixel check failed")
                ssDiff = None

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
