#! /usr/bin/env python3

"""
TIFF to JP2 workflow for Middeleeuwse Handschriften
"""

import os
import sys ## TEST
import shutil
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
        # List of input extensions that will be converted to JP2
        self.extensionsIn = ["tif", "tiff"]
        # Compression profile (name only, path is added later)
        self.compressionProfile = "KB_MASTER_LOSSLESS_01/01/2015"
        # Schematron schema used for properties check
        self.schema = "kbMaster_2015.sch"
        # Delimiter used in input concordance tables
        self.delimiterIn = ";"
        # Delimiter used in summary file and output concordance tables
        self.delimiterOut = ";"
        # Summary file (name only, path is added later)
        self.summaryFile = "summary.csv"
        # Checksum file (name only, path is added later)
        self.checksumFile = "checksums.sha256"
        # Input batch directory
        self.dirIn = None
        # Output batch directory
        self.dirOut = None
        # Configuration path
        self.configPath = None
        # Configuratiojn dictionary
        self.configDict = None
        # Grok instance
        self.grokInstance = None

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
            writer = csv.writer(fSum, delimiter=self.delimiterOut)
            row = [fileIn,
                fileOut,
                successGrok,
                pallettedFlag,
                successPixelCheck,
                successJpylyzerCheck,
                schTestsFailedStr]
            writer.writerow(row)


    def copyDir(self, dirIn):
        """Copy input dir to same relative location in output batch"""

        dirPathInRel = os.path.relpath(dirIn, start=self.dirIn)
        dirPathIn = os.path.abspath(os.path.join(self.dirIn, dirPathInRel))
        dirPathOut = os.path.abspath(os.path.join(self.dirOut, dirPathInRel))
        try:
            shutil.copytree(dirPathIn, dirPathOut, dirs_exist_ok = True)
        except Exception:
            logging.error("copying data from directory {} to {} resulted in an exception".format(dirPathIn, dirPathOut))


    def updateCTables(self, dirIn):
        """Update concordance tables"""

        dirPathInRel = os.path.relpath(dirIn, start=self.dirIn)
        dirPathIn = os.path.abspath(os.path.join(self.dirIn, dirPathInRel))
        dirPathOut = os.path.abspath(os.path.join(self.dirOut, dirPathInRel))

        # Create output directory
        if not os.path.isdir(dirPathOut):
            os.makedirs(dirPathOut)

        files = os.listdir(dirPathIn)
        for f in files:
            fileIn = os.path.join(dirPathIn, f)
            fileOut = os.path.join(dirPathOut, f)
            fileExtension = os.path.splitext(f)[1]
            fileExtension = fileExtension.upper().strip('.')

            if os.path.isfile(fileIn) and fileExtension == "CSV":
                self.updateCTable(fileIn, fileOut)


    def updateCTable(self, fileIn, fileOut):
        """Update concordance table"""

        # TODO: might not work for file references that include paths
        listOut = []
        rowIndex = 0
        with open(fileIn, 'r', newline='', encoding='utf-8') as fIn:
            reader = csv.reader(fIn, delimiter=self.delimiterIn)
            for row in reader:
                if rowIndex == 0:
                    # Header line
                    listOut.append(row)
                    rowIndex += 1
                else:
                    rowOut = []
                    for fNameIn in row:
                        pre, ext = os.path.splitext(fNameIn)
                        ext = ext.strip(".").upper()
                        if ext in self.extensionsIn:
                            fNameOut = "{}.{}".format(pre, "jp2")
                        else:
                            fNameOut = fNameIn
                        rowOut.append(fNameOut)
                    rowIndex += 1
                    listOut.append(rowOut)

        try:
            with open(fileOut, 'w', newline='', encoding='utf-8') as fOut:
                writer = csv.writer(fOut, delimiter=self.delimiterOut)
                writer.writerows(listOut)
        except Exception:
            logging.error("couldn't write updated concordance table to {}".format(fileOut))


    def processBatch(self):
        """Process a batch"""

        # Convert list of input file extensions to upper case
        self.extensionsIn = [extension.upper() for extension in self.extensionsIn]

        # Add path to Schematron schema for properties check
        self.schema = os.path.join(self.configPath, "schemas", self.schema)

        # Start Grok class instance
        self.grokInstance = grok.Grok()
        self.grokInstance.configDict = self.configDict
        self.grokInstance.configure()
        logging.info("grk_compress version: {}".format(self.grokInstance.version))
        self.grokInstance.compressionProfile = self.compressionProfile

        # Add path to summary file
        self.summaryFile = os.path.join(self.dirOut, self.summaryFile)

        # Add path to checksum file
        self.checksumFile = os.path.join(self.dirOut, self.checksumFile)

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
            writer = csv.writer(fSum, delimiter=self.delimiterOut)
            writer.writerow(summaryHeadings)

        # Iterate over directories and files in batch
        for dirname, dirnames, filenames in os.walk(self.dirIn):
            for subdirname in dirnames:
                thisDirectory = os.path.join(dirname, subdirname)
                if subdirname == "Pakbon":
                    # Files in Pakbon directory are copied without modification
                    self.copyDir(thisDirectory)
                if subdirname == "Concordantie":
                    # Update concordance tables
                    self.updateCTables(thisDirectory)

            for filename in filenames:
                if filename.startswith("._"):
                    # Ignore AppleDouble resource fork files (identified here by name)
                    pass
                else:
                    thisFile = os.path.join(dirname, filename)
                    thisExtension = os.path.splitext(thisFile)[1]
                    thisExtension = thisExtension.upper().strip('.')
                    if thisExtension in self.extensionsIn:
                        self.processImage(thisFile)
