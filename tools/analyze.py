import os
from PIL import Image

# vars
dirs = ("./images/test/", "./images/train/")
ext = ('.jpg')
files = []
resolutions = {}

# collect files
for dirname in dirs:
	for filename in os.listdir(dirname):
		if filename.endswith(ext):
			files.append(dirname + filename)

# collect sizes
for filename in files:
	im = Image.open(filename)
	w, h = im.size

	# TODO: add chart?
	if f"{w},{h}" not in resolutions.keys():
		resolutions[f"{w},{h}"] = 1
	else:
		resolutions[f"{w},{h}"] += 1

# sort
resolutions = sorted(resolutions.items(), key=lambda x: x[1])

# print
for res in resolutions:
	print(f"{res[1] / len(files) * 100:.1f}% - {res[0]}")