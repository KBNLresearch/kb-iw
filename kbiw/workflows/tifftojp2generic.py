#! /usr/bin/env python3

"""
Generic TIFF to JP2 workflow
"""

import os
import csv
import hashlib
import logging
from .. import shared
from .. import grok
from .. import pixelcheck
from .. import propertiescheck

class workflow:
    """workflow class"""

    def __init__(self):
        """initialise workflow class instance"""
        self.dirIn = ""
        self.dirOut = ""
        self.configPath = ""
        self.configDict = ""
        self.compressionProfile = ""
        self.grokInstance = ""
        self.schema = ""
        self.outDelimiter = ""
        self.summaryFile = ""
        self.checksumFile = ""


    def processImage(self, fileIn):
        """Process one image"""
        successGrok = False
        successPixelCheck = False
        successJpylyzerCheck = False
        schTestsFailedStr = ""
        fileNameIn = os.path.basename(fileIn)
        filePathIn = os.path.dirname(fileIn)
        filePathInRel = os.path.relpath(filePathIn, start=self.dirIn)
        filePathOut = os.path.abspath(os.path.join(self.dirOut, filePathInRel))

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
        self.grokInstance.imageIn = fileIn
        self.grokInstance.jp2Out = fileOut

        self.grokInstance.compress()
        logging.info("grk_compress exit status: {}".format(self.grokInstance.status))
        if self.grokInstance.status == 0:
            successGrok = True
            logging.info("grok.compress completed successfully")
        elif self.grokInstance.status != 0:
            logging.error("abnormal grk_compress exit status")
        if not self.grokInstance.success:
            logging.error("grok.compress function resulted in an exception")

        logging.info("grk_compress stdout: {}".format(self.grokInstance.out))
        logging.info("grk_compress stderr: {}".format(self.grokInstance.errors))

        if successGrok:

            # Analyze JP2 with Jpylyzer and evaluate output against Schematron policy
            # TODO this now fails on xmlBox test because Grok doesn't support this (perhaps relax specs?)
            status, schTestsFailed, jpTestsFailed, pallettedFlag = propertiescheck.propertiesCheck(fileOut, self.schema)

            if status == "pass":
                successJpylyzerCheck = True
                logging.info("image conforms to Schematron rules")
            else:
                # Add failed tests to pipe-delimited string that is included in summary file
                schTestsFailedOut = []
                for schtest in schTestsFailed:
                    schTestsFailedOut.append(schtest[0])

                schTestsFailedStr = '|'.join(schTestsFailedOut)
                logging.warning("image does not conform to Schematron rules")

            try:
                # Check on pixel values (skip for paletted images, because LibVips can't handle paletted JP2s)
                if not pallettedFlag:
                    ssDiff = pixelcheck.sumSqDiff(fileIn, fileOut)
                    if ssDiff == None:
                        logging.error("pixel check failed with exception")
                    if ssDiff == 0:
                        logging.info("pixel values of input and output images are identical")
                        successPixelCheck = True
                    else:
                        logging.warning("pixel values of input and output images are not identical")
                    logging.info("Sum of squared pixel differences: {}".format(ssDiff))
                else:
                    ssDiff = None
                    logging.warning("paletted image, skipped pixel check")

            except Exception:
                logging.error("pixel check failed")
                ssDiff = None

            # Calculate checksum (SHA-256)
            checksum = shared.generate_file_sha256(fileOut)

            # File reference, relative to output directory
            fileOutRel = os.path.relpath(fileOut, start=self.dirOut)

            # Construct checksum line, following https://superuser.com/a/1566139/681049
            checksumLine = "{}  {}\n".format(checksum, fileOutRel)

            # Write checksum line to file
            with open(self.checksumFile, 'a', newline='', encoding='utf-8') as fC:
                fC.write(checksumLine)

        # Write outcomes of QA checks to summary file
        with open(self.summaryFile, 'a', newline='', encoding='utf-8') as fSum:
            writer = csv.writer(fSum, delimiter=self.outDelimiter)
            row = [fileIn,
                fileOut,
                successGrok,
                pallettedFlag,
                successPixelCheck,
                successJpylyzerCheck,
                schTestsFailedStr]
            writer.writerow(row)


    def processBatch(self):
        """Process a batch"""

        # List of file extensions to process (upper case for case insensitive processing later)
        extensions = ["tif", "tiff"]
        extensions = [extension.upper() for extension in extensions]

        # Schematron schema for properties check
        self.schema = os.path.join(self.configPath, "schemas", "kbMaster_2015.sch")

        # Output delimiter
        self.outDelimiter = ";"

        # Compression profile
        self.compressionProfile = "KB_MASTER_LOSSLESS_01/01/2015"

        # Start Grok class instance
        self.grokInstance = grok.Grok()
        self.grokInstance.configDict = self.configDict
        self.grokInstance.configure()
        logging.info("grk_compress version: {}".format(self.grokInstance.version))
        self.grokInstance.compressionProfile = self.compressionProfile

        # Summary file
        self.summaryFile = os.path.join(self.dirOut, "summary.csv")

        # Checksum file
        self.checksumFile = os.path.join(self.dirOut, "checksums.sha256")

        # Remove any previous summary / checksum file instances
        if os.path.isfile(self.summaryFile):
            os.remove(self.summaryFile)
        if os.path.isfile(self.checksumFile):
            os.remove(self.checksumFile)

        # Write header to summary file
        summaryHeadings = ["fileIn",
                        "fileOut",
                        "successGrok",
                        "palettedImage",
                        "successPixelCheck",
                        "successJpylyzerCheck",
                        "failedJpylyzerChecks"]

        with open(self.summaryFile, 'w', newline='', encoding='utf-8') as fSum:
            writer = csv.writer(fSum, delimiter=self.outDelimiter)
            writer.writerow(summaryHeadings)

        for dirname, dirnames, filenames in os.walk(self.dirIn):
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
                    if thisExtension in extensions:
                        self.processImage(thisFile)
