import glob, os

exceptions = ['classes'] # .txt files that will be excluded
removed = 0
os.chdir("./images/")
for filename in glob.glob("*.txt"):
	basename = os.path.splitext(filename)[0]

	if basename in exceptions:
		continue

	imgfile = basename + '.png'
	if not os.path.isfile(imgfile):
		imgfile = basename + '.jpg' # try jpg

	with open(filename) as f:
		content = f.read()

	# remove, if file is empty or if there's no image file
	if not content.strip() or not os.path.isfile(imgfile):
		os.remove(filename)

		if os.path.isfile(imgfile):
			os.remove(imgfile)

		print(f"File {filename} removed ...")
		removed += 1

print("===============================")
if removed:
	print(f"Total files removed: {removed}")
else:
	print("No files to be removed found.")