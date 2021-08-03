#!/usr/local/bin/python3

import sys, math
from PIL import Image, ImageDraw

filename_in = sys.argv[1]
filename_out = sys.argv[2]

data = bytearray(open(filename_in, 'rb').read())

signature = data[:8]
version = data[8]
notracks = data[9]
tracksize = data[10] | data[11] << 8

size = 40000
img = Image.new('RGB', (size, size), color = 'white')
draw = ImageDraw.Draw(img)

track_distance = size / 150

print("signature {}, version {}, notracks {}, tracksize {}, track_distance {}".format(signature, version, notracks, tracksize, track_distance))

for i in range(0, notracks):
	trackno = i / 2 + 1
	offset = data[12 + 4 * i] | data[12 + 4 * i + 1] << 8 | data[12 + 4 * i + 2] << 16 | data[12 + 4 * i + 3] << 24
	speed = data[0x15c + 4 * i] | data[0x15c + 4 * i + 1] << 8 | data[0x15c + 4 * i + 2] << 16 | data[0x15c + 4 * i + 3] << 24
	if not offset:
		continue

	len = data[offset] | data[offset + 1] << 8

	sectorlen = len * 8
	radius = size * .99 / 2 - trackno * track_distance
	radius1 = radius - track_distance / 2.1
	radius2 = radius + track_distance / 2.1

	# G64 files built by tools might not contain the tail gap data,
	# so if there is significantly less data on the track than we expect,
	# don't scale it to 360 degrees, but leave the tail area empty.
	sector_capacity = 200000 / [32, 30, 28, 26][speed] * 8
	if float(sectorlen) / sector_capacity > .993:
		sector_capacity = sectorlen

	print("track {}, offset {}, size {}, speed {}, capacity {}".format(trackno, offset, len, speed, sector_capacity / 8))

	for i in range(0, sectorlen):
		angle = float(i) / sector_capacity * 2 * math.pi
		x1 = int(round(size / 2 + radius1 * math.sin(angle)))
		y1 = int(round(size / 2 + radius1 * math.cos(angle)))
		x2 = int(round(size / 2 + radius2 * math.sin(angle)))
		y2 = int(round(size / 2 + radius2 * math.cos(angle)))
		byte = data[int(offset + i / 8) + 2]
		if byte == 0x00:
			value = (0, 0, 0xff) # empty = blue
		elif byte == 0xff:
			value = (0xff, 0, 0) # sync = red
		else:
			pixel = ((byte >> (i % 7)) & 1) * 255
			value = (0, pixel, 0) # shades of green

		draw.line((x1, y1, x2, y2), fill = value, width = 2)

img = img.resize((int(size / 16), int(size / 16)), Image.ANTIALIAS)
img.save(filename_out)
