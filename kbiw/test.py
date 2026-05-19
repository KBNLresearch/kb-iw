import os
import sys
import csv
import logging

class test:

    def __init__(self):
        """initialise workflow class instance"""
        self.delimiterIn = ";"
        self.delimiterOut = ";"
        self.batchManifest = "/home/johan/kb/digitalisering/tifftojp2/mh-small-jp2/manifest.csv"
        self.dirOut = "/home/johan/kb/digitalisering/tifftojp2/mh-small-jp2"
        self.noErrors = 0
        self.noWarnings = 0

    def concordanceCheck(self):
        """Cross-check concordance tables against batch manifest"""
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
                        # Directory of this images follows from file name
                        nameComponents = imageTarget.split(".")[0].split("_")
                        targetDir = "{}_{}_{}".format(nameComponents[0], nameComponents[2], nameComponents[3])
                        # Construct full path in corresponding batch manifest value
                        imageTargetFullPath = os.path.join("Targets", targetDir, imageTarget)
                        imagesCTable.append(imageTargetFullPath)

                rowIndex += 1

            for image in imagesCTable:
                # Check against batch manifest
                if not image in imagesManifest:
                    logging.error("image {} from not found in batch manifest".format(image))
                    self.noErrors += 1
                # Add image to combined list of image references from all concordance tables
                imagesAllCTables.append(image)

        # Reverse check
        for image in imagesManifest:
            if not image in imagesAllCTables:
                logging.error("image {} from batch manifest not referenced in any concordance table".format(image))
                self.noErrors += 1

def main():

    # Set up logging
    logging.basicConfig(handlers=[logging.StreamHandler(sys.stdout)],
                                  level=logging.INFO,
                                  format='%(asctime)s - %(levelname)s - %(message)s')

    wf = test()
    wf.concordanceCheck()


if __name__ == "__main__":
    main()
