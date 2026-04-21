#! /usr/bin/env python3

import pyvips


print("######## TEST pyvips.API_mode: #####")
pyvips.API_mode = False
print(pyvips.API_mode)

image1 = "/home/johan/kb/digitalisering/tifftojp2/test-tiff/bulls/MMIISG26_COL_OZ08_20230807_0725.tif"
#image2 = "/home/johan/kb/digitalisering/tifftojp2/test-tiff/bulls/MMIISG26_COL_OZ08_20230807_0725.tif"

image2 = "/home/johan/kb/digitalisering/tifftojp2/test-jp2/bulls/MMIISG26_COL_OZ08_20230807_0725.jp2"


im1 = pyvips.Image.new_from_file(image1)
im2 = pyvips.Image.new_from_file(image2)
# Compute difference image
diff = im1.subtract(im2)
# Compute stats from differences image and convert to nested list
stats = diff.stats().tolist()
print(stats)

#ssDiff = stats[0][3]

