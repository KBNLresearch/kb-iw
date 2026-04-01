#! /usr/bin/env python3

"""Do properties check based on Jplyzer output and Schematron rules
"""
import logging
import xml.etree.ElementTree as ET
from jpylyzer import jpylyzer
from lxml import isoschematron
from lxml import etree


def extractSchematron(report):
    """Parse output of Schematron validation and extract failed tests"""

    testsFailed = []

    for elem in report.iter():
        if elem.tag == "{http://purl.oclc.org/dsdl/svrl}failed-assert":

            # Extract test definition and text description
            test = elem.get('test')

            for subelem in elem.iter():
                if subelem.tag == "{http://purl.oclc.org/dsdl/svrl}text":
                    description = (subelem.text)
            testsFailed.append([test, description])

    return testsFailed


def extractJpylyzer(resultJpylyzer):
    """Parse output of Jpylyzer and extract failed validation tests"""

    testsFailed = []
    validationOutcome = resultJpylyzer.find("isValid").text

    if validationOutcome == "False":

        # Locate test elements

        for element in resultJpylyzer.iter():
            if element.tag == "tests":
                testsElt = element

        # Iterate over tests element and report names of all
        # tags thatcorrespond to tests that failed

        tests = list(testsElt.iter())

        for j in tests:
            if j.text == "False":
                testsFailed.append(j.tag)

    return testsFailed


def main():
    """Do properties check on one JP2"""

    JP2 = "/home/johan/kb/digitalisering/tifftojp2/test-jp2/bulls/MMIISG26_COL_OZ08_20230807_0725.jp2"
    JP2 = "/home/johan/jpylyzer-test-files/files/data_missing_in_last_tilepart.jp2"
    schema = "/home/johan/.config/jp2batchconverter/schemas/kbMaster_2015.sch"
    #schema = "/home/johan/.config/jp2batchconverter/schemas/kbAccess_2015.sch"

    # Initialise status (pass/fail)
    status = "pass"

    # Initialise empty text string for error log output
    ptOutString = ""

    # Run jpylyzer on image and write result to text file
    try:
        resultJpylyzer = jpylyzer.checkOneFile(JP2)
        resultAsXML = ET.tostring(resultJpylyzer, 'UTF-8', 'xml')
        ## TEST
        with open('jpylyzer.xml', 'wb') as fj:
            fj.write(resultAsXML)
        ## TEST

        #print(resultAsXML)
    except Exception:
        status = "fail"
        logging.error("error while running jpylyzer")

    try:
        # Start Schematron magic ...

        schema_doc = etree.parse(schema)
        schematron = isoschematron.Schematron(schema_doc,
                                              store_report=True)

        # Reparse jpylyzer XML with lxml since using ET object
        # directly doesn't work
        resJpylyzerLXML = etree.fromstring(resultAsXML)

        ## TEST
        #print(resJpylyzerLXML)
        ## TEST

        # Validate jpylyzer output against schema
        schemaValidationResult = schematron.validate(resJpylyzerLXML)
        report = schematron.validation_report
        ## TEST
        #print(report)
        ## TEST

    except Exception:
        status = "fail"
        logging.error("error while running Schematron")

    # Parse output of Schematron validation and extract
    # interesting bits
    try:
        schematronTestsFailed = extractSchematron(report)
        ## TEST
        print(schematronTestsFailed )
        ## TEST
    except Exception:
        raise
        status = "fail"
        logging.error("error while parsing Schematron report")

    # Parse jpylyzer XML output and extract info on failed tests
    # in case image is not valid JP2
    try:
        jpylyzerTestsFailed = extractJpylyzer(resultJpylyzer)
        ## TEST
        print(jpylyzerTestsFailed)
        ## TEST
    except Exception:
        status = "fail"
        logging.error("error while parsing jpylyzer output")

    return status, schematronTestsFailed, jpylyzerTestsFailed

if __name__ == "__main__":
    main()




