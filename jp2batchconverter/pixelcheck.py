#! /usr/bin/env python3

"""Compare pixel values from pair of images
"""

import pyvips

def sumSqDiff(image1, image2):
    """ Returns sum of squared difference between two images"""

    print("######## TEST pyvips.API_mode: #####")
    print(pyvips.API_mode)

    try:
        im1 = pyvips.Image.new_from_file(image1)
        im2 = pyvips.Image.new_from_file(image2)
        # Compute difference image
        diff = im1.subtract(im2)
        # Compute stats from differences image and convert to nested list
        stats = diff.stats().tolist()
        # First child list contains aggregated statistics for all bands,
        # subsequent child lists contain statistics for individual bands.
        # Documented here:
        #
        # https://www.libvips.org/API/8.17/method.Image.stats.html
        #
        # Statistics for each list, in order:
        # minimum, maximum, sum, sum of squares, mean, standard deviation,
        # x coordinate of minimum, y coordinate of minimum,
        # xcoordinate of maximum, y coordinate of maximum.
        #
        # Return sum of squared differences (aggregated for all bands)
        ssDiff = stats[0][3]
    except Exception:
        ssDiff = None

    return ssDiff
