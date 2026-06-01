#! /usr/bin/env python3

"""
TIFF to JP2 workflow for Middeleeuwse Handschriften
"""

import os
import shutil
import csv
import hashlib
import logging
import exiftool
from .. import shared
from .. import grok
from .. import pixelcheck
from .. import propertiescheck
from .. import concordance

class workflow:
    """workflow class"""

    def __init__(self):
        """initialise workflow class instance"""
        # List of input extensions that will be converted to JP2
        self.extensionsIn = ["tif", "tiff"]
        # Compression profile (name only, path is added later)
        self.compressionProfile = "KB_MASTER_LOSSLESS_01/01/2015"
        # Schematron schema used for properties check
        self.schema = "kbMaster_2026.sch"
        # Delimiter used in input concordance tables
        self.delimiterIn = ";"
        # Delimiter used in summary file and output concordance tables
        self.delimiterOut = ";"
        # Batch manifest (name only, path is added later)
        self.batchManifest = "manifest.csv"
        # Summary file (name only, path is added later)
        self.summaryFile = "summary.txt"
        # Checksum file (name only, path is added later)
        self.checksumFile = "checksums.sha256"
        # Number of errors encountered during workflow
        self.noErrors = 0
        # Number of warnings encountered during workflow
        self.noWarnings = 0
        # Input batch directory (set in main kbiw.py module)
        self.dirIn = None
        # Output batch directory (set in main kbiw.py module)
        self.dirOut = None
        # Configuration path (set in main kbiw.py module)
        self.configPath = None
        # Configuration dictionary (set in main kbiw.py module)
        self.configDict = None
        # Grok instance (set in processBatch function)
        self.grokInstance = None
        # ExifTool instance (set in processBatch function)
        self.etInstance = None


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

        # Start ExifTool instance, using executables as defined in configuration file
        self.etInstance = exiftool.ExifToolHelper(executable=self.configDict["exifToolExecutable"])

        # Add paths to batch manifest, checksum and summary files
        self.batchManifest = os.path.join(self.dirOut, self.batchManifest)
        self.checksumFile = os.path.join(self.dirOut, self.checksumFile)
        self.summaryFile = os.path.join(self.dirOut, self.summaryFile)

        # Remove any previous batch manifest / checksum / summary file instances
        if os.path.isfile(self.batchManifest):
            os.remove(self.batchManifest)
        if os.path.isfile(self.checksumFile):
            os.remove(self.checksumFile)
        if os.path.isfile(self.summaryFile):
            os.remove(self.summaryFile)

        # Write header to batch manifest
        manifestHeadings = ["image",
                        "successGrok",
                        "successExifTool",
                        "palettedImage",
                        "successPixelCheck",
                        "successJpylyzerCheck",
                        "failedJpylyzerChecks"]

        with open(self.batchManifest, 'w', newline='', encoding='utf-8') as fManifest:
            writer = csv.writer(fManifest, delimiter=self.delimiterOut)
            writer.writerow(manifestHeadings)

        # Iterate over directories and files in batch
        for dirname, dirnames, filenames in os.walk(self.dirIn):
            for subdirname in dirnames:
                thisDirectory = os.path.join(dirname, subdirname)
                if subdirname == "Pakbon":
                    # Files in Pakbon directory are copied without modification
                    self.copyDir(thisDirectory)
                if subdirname == "Access_Renamed":
                    # Files in Access_Renamed directory are copied without modification
                    # TODO: check if this needs to be included at all!
                    self.copyDir(thisDirectory)
                if subdirname == "Concordantie":
                    # Update concordance tables
                    myConcordance = concordance.Concordance(thisDirectory,
                                                            self.dirIn,
                                                            self.dirOut,
                                                            self.delimiterIn,
                                                            self.delimiterOut,
                                                            self.extensionsIn,
                                                            self.batchManifest)
                    myConcordance.updateCTables()

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

        # Cross check entries in concordance tables with batch manifest
        myConcordance.concordanceCheck()

        # Add any errors from concordance updating / checking to general error count
        self.noErrors += myConcordance.noErrors

        # Number of errors, warnings to log
        logging.info("workflow completed with {} errors and {} warnings".format(self.noErrors, self.noWarnings))

        # Write summary file
        with open(self.summaryFile, 'w', newline='', encoding='utf-8') as fSum:
            fSum.write("Grok version: {}\n".format(self.grokInstance.version))
            fSum.write("Errors: {}\n".format(self.noErrors))
            fSum.write("Warnings: {}\n".format(self.noWarnings))
            fSum.write("See batch manifest and log file for details on errors and warnings\n")


    def processImage(self, fileIn):
        """Process one image"""
        successGrok = False
        successExifTool = False
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
            self.noErrors += 1
        if not self.grokInstance.success:
            logging.error("grok.compress function resulted in an exception")
            self.noErrors += 1

        logging.info("grk_compress stdout: {}".format(self.grokInstance.out))
        logging.info("grk_compress stderr: {}".format(self.grokInstance.errors))

        if successGrok:

            # Read metadata from input TIFF and write as XMP block to JP2
            # Adapted from: https://exiftool.org/forum/index.php?topic=2922.0
            try:
                self.etInstance.execute("-tagsfromfile", fileIn, "-all>xmp:all", "-overwrite_original", fileOut)
                successExifTool = True
            except Exception:
                logging.error("ExifTool failed to copy metadata from TIFF to JP2")
                successExifTool = False
                self.noErrors += 1

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
                self.noWarnings += 1

            try:
                # Check on pixel values (skip for paletted images, because LibVips can't handle paletted JP2s)
                if not pallettedFlag:
                    ssDiff = pixelcheck.sumSqDiff(fileIn, fileOut)
                    if ssDiff == None:
                        logging.error("pixel check failed with exception")
                        self.noErrors += 1
                    if ssDiff == 0:
                        logging.info("pixel values of input and output images are identical")
                        successPixelCheck = True
                    else:
                        logging.warning("pixel values of input and output images are not identical")
                        self.noWarnings += 1
                    logging.info("Sum of squared pixel differences: {}".format(ssDiff))
                else:
                    ssDiff = None
                    logging.warning("paletted image, skipped pixel check")
                    self.noWarnings += 1

            except Exception:
                logging.error("pixel check failed")
                ssDiff = None
                self.noErrors += 1

            # Calculate checksum (SHA-256)
            checksum = shared.generate_file_sha256(fileOut)

            # File reference, relative to output directory
            fileOutRel = os.path.relpath(fileOut, start=self.dirOut)

            # Construct checksum line, following https://superuser.com/a/1566139/681049
            checksumLine = "{}  {}\n".format(checksum, fileOutRel)

            # Write checksum line to file
            with open(self.checksumFile, 'a', newline='', encoding='utf-8') as fC:
                fC.write(checksumLine)

        # Write outcomes of QA checks to batch manifest
        with open(self.batchManifest, 'a', newline='', encoding='utf-8') as fManifest:
            writer = csv.writer(fManifest, delimiter=self.delimiterOut)
            row = [fileOutRel,
                successGrok,
                successExifTool,
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
        logging.info("copying directory {} to {}".format(dirPathIn, dirPathOut))
        try:
            shutil.copytree(dirPathIn, dirPathOut, dirs_exist_ok = True)
        except Exception:
            logging.error("copying data from directory {} to {} resulted in an exception".format(dirPathIn, dirPathOut))
            self.noErrors += 1


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
        logging.info("updating concordance table {} to {}".format(fileIn, fileOut))
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
            self.noErrors += 1


    def concordanceCheck(self):
        """Cross-check concordance tables against batch manifest including reverse check)"""
        # TODO: code assumes fixed position + order of columns in concordance tables
        # verify if this is correct. If not, use column names.

        logging.info("Checking concordance tables against batch manifest")

        with open(self.batchManifest, 'r', newline='', encoding='utf-8') as fMan:
            reader = csv.reader(fMan, delimiter=self.delimiterOut)
            manifestData = list(reader)

        # List that will store all image references in the batch manifest
        imagesManifest = []

        # List that will store all image references in all concordance tables
        imagesAllCTables = []
        rowIndex = 0
        for row in manifestData:
            if rowIndex > 0:
                imagesManifest.append(row[0])
            rowIndex += 1

        concordanceDir = os.path.join(self.dirOut, "Concordantie")

        # Stop here if concordance dir doesn't exist'
        if not os.path.isdir(concordanceDir):
            logging.error("concordance directory {} does not exist".format(concordanceDir))
            self.noErrors += 1
            return
        cTables = os.listdir(concordanceDir)
        for cTable in cTables:
            # First part of file name refers to directory in "Signaturen"
            sigDir = cTable.split("_")[0]
            masterDirPath = os.path.join("Signaturen", sigDir, "Master")
            cTable = os.path.join(concordanceDir, cTable)
            with open(cTable, 'r', newline='', encoding='utf-8') as fCTab:
                reader = csv.reader(fCTab, delimiter=self.delimiterOut)
                cTabData = list(reader)

            # List that will store all image references in this concordance table
            imagesCTable = []

            rowIndex = 0
            for row in cTabData:
                if rowIndex > 0:
                    # First column: master image
                    imageMaster = row[0]
                    # Add masterDirPath to get corresponding batch manifest value
                    imageMasterFullPath = os.path.join(masterDirPath, imageMaster)
                    imagesCTable.append(imageMasterFullPath)

                    # Columns 3 - 6 refer to target images (column 2 refers to access images, which are not in manifest)
                    for i in range(2, 6):
                        imageTarget = row[i]
                        # Directory of this image follows from file name
                        try:
                            nameComponents = imageTarget.split(".")[0].split("_")
                        except IndexError:
                            nameComponents = []
                        try:
                            targetDir = "{}_{}_{}".format(nameComponents[0], nameComponents[2], nameComponents[3])
                            # Construct full path in corresponding batch manifest value
                            imageTargetFullPath = os.path.join("Targets", targetDir, imageTarget)
                            imagesCTable.append(imageTargetFullPath)
                        except IndexError:
                            pass

                rowIndex += 1

            for image in imagesCTable:
                # Check against batch manifest
                if not image in imagesManifest:
                    logging.error("image {} not found in batch manifest".format(image))
                    self.noErrors += 1
                # Add image to combined list of image references from all concordance tables
                imagesAllCTables.append(image)

        # Reverse check
        for image in imagesManifest:
            if not image in imagesAllCTables:
                logging.error("image {} from batch manifest not referenced in any concordance table".format(image))
                self.noErrors += 1
