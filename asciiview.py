#!/usr/bin/python3
from PIL import Image, ImageFilter, ImageChops, ImageStat, ImageEnhance, ImageOps
import argparse
import shutil
import numpy
import string
import sys
import math

parser = argparse.ArgumentParser(description='Turn images into text.')
parser.add_argument('-r', '--raw', action='store_true', help='don\'t apply pre-processing to the image before converting to text')
parser.add_argument('-i', '--invert', action='store_true', help='invert image before converting to text')
parser.add_argument('-o', '--output', default=sys.stdout, type=argparse.FileType('w'), metavar='FILE', help='file to output to')
resize_mode = parser.add_mutually_exclusive_group()
resize_mode.add_argument('--scale', action='store_true', help='resize image to fit in terminal window. Aspect ratio preserved')
resize_mode.add_argument('--fit', action='store_true', help='resize image to fit terminal window in both dimensions')
resize_mode.add_argument('--width', nargs=None, type=int, help='output width in characters (columns). Aspect ratio preserved')
resize_mode.add_argument('--height', nargs=None, type=int, help='output height in characters (lines). Aspect ratio preserved')
resize_mode.add_argument('--size', nargs=2, type=int, metavar=('WIDTH', 'HEIGHT'), help='output size in columns and lines')
parser.add_argument('image', help='image to be processed')

args = parser.parse_args()

# codepage_path = sys.argv[1]
codepage_path = "images/Codepage-437.png"
print("READING CODEPAGE")
codepage = Image.open(codepage_path).convert('RGB')

character_bmps = {}

print("GENERATING CHARACTERS")
for c in (string.ascii_letters + string.digits + string.punctuation + ' '):
    ascii_code = ord(c)
    bounding_box = ((ascii_code % 32) * 9, math.floor(ascii_code / 32) * 16, (ascii_code % 32) * 9 + 9, math.floor(ascii_code / 32) * 16 + 16)
    character_bmps[ascii_code] = codepage.crop(bounding_box)

print("READING IMAGE")
image = Image.open(args.image).convert('RGB')
filtered = image

print("RESIZING IMAGE")
tsize = shutil.get_terminal_size()
ar = filtered.width / filtered.height

if args.scale:
    w = tsize.columns
    h = math.floor((w/ar*9)/16)

    if h > tsize.lines:
        h = tsize.lines - 1
        w = math.floor((h*ar*16)/9)

elif args.fit:
    w = tsize.columns
    h = tsize.lines

elif args.width:
    w = args.width
    h = math.floor((w/ar*9)/16)

elif args.height:
    h = args.height
    w = math.floor((h*ar*16)/9)

elif args.size:
    w, h = args.size

else:
    w = math.floor(filtered.width/9)
    h = math.floor(filtered.height/16)

filtered = filtered.resize((w*9, h*16))
width, height = filtered.size

if args.invert:
    filtered = ImageOps.invert(filtered)

if not args.raw:
    print("PRE-PROCESSING IMAGE")
    filtered = ImageOps.autocontrast(filtered)
    filtered = filtered.filter(ImageFilter.CONTOUR)
    filtered = ImageOps.invert(filtered)
    filtered = ImageChops.subtract(filtered, ImageChops.constant(filtered, 50).convert('RGB'))
    filtered = filtered.filter(ImageFilter.BLUR)
    filtered = ImageEnhance.Brightness(filtered).enhance(2)
    filtered = ImageEnhance.Contrast(filtered).enhance(2)
    filtered = filtered.filter(ImageFilter.BLUR)
    filtered = ImageEnhance.Brightness(filtered).enhance(2)
    filtered = ImageEnhance.Contrast(filtered).enhance(2)

#filtered.show()

s = ""

print("MATCHING")
for y in range(0, math.floor(height/16)):
    for x in range(0, math.floor(width/9)):
        bounding_box = (x * 9, y * 16, x * 9 + 9, y * 16 + 16)
        selection = filtered.crop(bounding_box)
        match = {}
        for bmp in character_bmps.keys():
            out = ImageChops.difference(character_bmps[bmp], selection)
            stat = ImageStat.Stat(out)
            match[bmp] = stat.sum
        best_match = sorted(match, key=match.get)[0]
        s += chr(best_match)
    print("Progress:{0:6.2f}%".format(100*y/math.floor(height/16)), end="\r")
    s += "\n"
print("DONE")
args.output.write(s)
