#! /usr/bin/env python3
"""Concordance table manipulation module"""

import os
import csv
import logging

class Concordance:
    """Concordance"""

    def __init__(self, dirConcordance, dirIn, dirOut, delimiterIn,
                 delimiterOut, extensionsIn, batchManifest):

        self.noErrors = 0
        self.dirConcordance = dirConcordance
        self.dirIn = dirIn
        self.dirOut = dirOut
        self.delimiterIn = delimiterIn
        self.delimiterOut = delimiterOut
        self.extensionsIn = extensionsIn
        self.batchManifest = batchManifest


    def updateCTables(self):
        """Update concordance tables"""

        dirPathInRel = os.path.relpath(self.dirConcordance, start=self.dirIn)
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
