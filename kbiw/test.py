#! /usr/bin/env python3


import sys
import logging
import pyvips

logging.basicConfig(handlers=[logging.StreamHandler(sys.stdout)],
                    level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

logging.info("libvips version: {}.{}.{}".format(pyvips.base.version(0), pyvips.base.version(1), pyvips.base.version(2)))
logging.info("API mode: {}".format(pyvips.API_mode))

#image1 = "/home/johan/kb/digitalisering/tifftojp2/test-tiff/bulls/MMIISG26_COL_OZ08_20230807_0725.tif"
image1 = "/home/johan/test/balloon_large.tif"
im1 = pyvips.Image.new_from_file(image1)
statistics = im1.stats()
