import glob, os, sys

# from => to
correction_table = (
	(0, 1), # fix ch
	(1, 0), # fix c
	(2, 3), # fix th
	(3, 2)  # fix t

)

exceptions = ['classes'] # .txt files that will be excluded
fixed = 0
os.chdir("./images/")
for filename in glob.glob("*.txt"):
	rewrite = False
	basename = os.path.splitext(filename)[0]

	if basename in exceptions:
		continue

	with open(filename) as f:
		lines = f.read().splitlines()

	for lk, lv in enumerate(lines):
		dt_data = lv.strip().split(" ")

		for patch in correction_table:
			# patch
			if str(dt_data[0]) == str(patch[0]):
				# print(f"Patch applied: {dt_data[0]} => {patch[1]}")
				dt_data[0] = str(patch[1])

				lines[lk] = " ".join(dt_data)

				rewrite = True
				break # patch found & applied, break

	if rewrite:
		with open(filename, 'w') as f:
			f.write("\n".join(lines))

		fixed += 1
		print(f"File {filename} fixed ...")


print("===============================")
if fixed:
	print(f"Total files fixed: {fixed}")
else:
	print("No files to be fixed found.")