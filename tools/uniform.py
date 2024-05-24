import os, sys
from PIL import Image
from lxml import etree
from pyquery import PyQuery as pq
from pathlib import Path

# vars
dirs = ("./images/test/", "./images/train/")
ext = ('.jpg')
files = []
resolutions = {}
uniform_target_resolution = 400 # height

# collect files
for dirname in dirs:
	for filename in os.listdir(dirname):
		if filename.endswith(ext):
			files.append(dirname + filename)

# resize the images
for filename in files:
	im = Image.open(filename)
	w, h = im.size

	xdiff = w / uniform_target_resolution # scale difference multiplier

	if w != uniform_target_resolution:
		# downscale/upscale
		new_width = int(uniform_target_resolution)
		new_height = int(uniform_target_resolution * h / w)

		im = im.resize((new_width, new_height), Image.ANTIALIAS)
		im.save(filename) # save resized

		# edit xml
		xmlfile = os.path.splitext(filename)[0] + '.xml'
		xml = pq(filename=xmlfile)

		xml("size > width").text(str(new_width))
		xml("size > height").text(str(new_height))

		xml("object > bndbox > xmin,\
			 object > bndbox > xmax,\
			 object > bndbox > ymin,\
			 object > bndbox > ymax").map(lambda i, e: pq(e).text(str(int(float(pq(e).text()) / xdiff))))

		# save edited xml file
		Path(xmlfile).write_text(
		    xml.outerHtml(),
		    encoding='utf-8'
		)

		# log
		print(f"File {filename} processed ...")