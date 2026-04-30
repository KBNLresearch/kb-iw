import pyvips

image1 = "/home/johan/test/0001535002.jp2"

im1 = pyvips.Image.new_from_file(image1, access="sequential")
stats = im1.stats().tolist()
