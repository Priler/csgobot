import glob, os, sys
from math import *
from tqdm import tqdm
import shutil

"""
@TODO
- Resumable?
- Ask for divide rule?
- Better progress bar.
"""

# input dirs
input_folders = [
	'./lstudio/allin/',
]

# base out dir
BASE_DIR_ABSOLUTE = "D:\\Python\\csgobot\\yolov8\\datasets\\"
OUT_DIR = './prepared/'

# out dirs
OUT_TRAIN = OUT_DIR + 'train/'
OUT_VAL = OUT_DIR + 'val/'
OUT_TEST = OUT_DIR + 'test/'

# config
coeff = [80, 10, 10]  # train/val/test
exceptions = ['classes']  # .txt files that will be excluded


# prepare
if int(coeff[0]) + int(coeff[1]) + int(coeff[2]) > 100:
	print("Overall coeff can't exceed 100%.")
	exit(1)


def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))

# print some info
print(f"Preparing images data by {coeff[0]}/{coeff[1]}/{coeff[2]} rule.")
print(f"Source folders: {len(input_folders)}")
print("Gathering data ...")

# collect in
source = {}
total_files = 0
for sf in input_folders:
	source.setdefault(sf, [])

	os.chdir(BASE_DIR_ABSOLUTE)
	os.chdir(sf)

	for filename in glob.glob("*.txt"):
		basename = os.path.splitext(filename)[0]

		if basename in exceptions:
			continue

		imgfile = basename + '.png'
		if not os.path.isfile(imgfile):
			imgfile = basename + '.jpg' # try jpg

			if not os.path.isfile(imgfile):
				continue # nothing found, skip

		source[sf].append(imgfile)
		total_files += 1

print(f"Total images: {total_files}")

# separate by train/val/test rule
train = {}
val = {}
test = {}
for sk, sv in source.items():
	chunks = 100
	train_chunk = floor(chunks * (coeff[0] / 100))
	val_chunk = floor(chunks * (coeff[1] / 100))
	test_chunk = floor(chunks * (coeff[2] / 100))
	# val_chunk = chunks - train_chunk

	#print(f"t: {train_chunk}\nv: {val_chunk}\nt: {test_chunk}")
	#sys.exit(1)

	train.setdefault(sk, [])
	val.setdefault(sk, [])
	test.setdefault(sk, [])
	for item in chunker(sv, chunks):
		train[sk].extend(item[0:train_chunk])
		val[sk].extend(item[train_chunk:100-test_chunk])
		test[sk].extend(item[100-test_chunk:])

	# print(f"Divide info: train({len(train[sk])}) val({len(val[sk])}) test({len(test[sk])})")

# copy source to prepared
train_sum = 0
val_sum = 0
test_sum = 0

for sk, sv in train.items():
	train_sum += len(sv)

for sk, sv in val.items():
	val_sum += len(sv)

for sk, sv in test.items():
	test_sum += len(sv)

# print some info
print(f"\nOverall TRAIN images count: {train_sum}")
print(f"Overall VAL images count: {val_sum}")
print(f"Overall TEST images count: {test_sum}")

os.chdir(BASE_DIR_ABSOLUTE)
print("\nCopying TRAIN source items to prepared folder ...")
for sk, sv in tqdm(train.items()):
	for item in tqdm(sv):
		basename = os.path.splitext(item)[0]

		imgfile_source = sk + item
		txtfile_source = sk + basename + '.txt'

		imgfile_dest = OUT_TRAIN + 'images/' + item
		txtfile_dest = OUT_TRAIN + 'labels/' + basename + '.txt'

		shutil.copyfile(imgfile_source, imgfile_dest)
		shutil.copyfile(txtfile_source, txtfile_dest)

os.chdir(BASE_DIR_ABSOLUTE)
print("\nCopying VAL source items to prepared folder ...")
for sk, sv in tqdm(val.items()):
	for item in tqdm(sv):
		basename = os.path.splitext(item)[0]

		imgfile_source = sk + item
		txtfile_source = sk + basename + '.txt'

		imgfile_dest = OUT_VAL + 'images/' + item
		txtfile_dest = OUT_VAL + 'labels/' + basename + '.txt'

		shutil.copyfile(imgfile_source, imgfile_dest)
		shutil.copyfile(txtfile_source, txtfile_dest)

os.chdir(BASE_DIR_ABSOLUTE)
print("\nCopying TEST source items to prepared folder ...")
for sk, sv in tqdm(test.items()):
	for item in tqdm(sv):
		basename = os.path.splitext(item)[0]

		imgfile_source = sk + item
		txtfile_source = sk + basename + '.txt'

		imgfile_dest = OUT_TEST + 'images/' + item
		txtfile_dest = OUT_TEST + 'labels/' + basename + '.txt'

		shutil.copyfile(imgfile_source, imgfile_dest)
		shutil.copyfile(txtfile_source, txtfile_dest)

# print some info
print("\nDONE!")