import sys, math
from PIL import Image, ImageDraw

filename_in = sys.argv[1]
filename_out = sys.argv[2]

data = bytearray(open(filename_in, 'rb').read())

signature = data[:8]
version = data[8]
notracks = data[9]
tracksize = data[10] | data[11] << 8

img = Image.new('RGB', (8000, 2000), color = 'white')
pixels = img.load()

x = 0
y = 0

for i in range(0, notracks):
	trackno = i / 2 + 1
	offset = data[12 + 4 * i] | data[12 + 4 * i + 1] << 8 | data[12 + 4 * i + 2] << 16 | data[12 + 4 * i + 3] << 24
	speed = data[0x15c + 4 * i] | data[0x15c + 4 * i + 1] << 8 | data[0x15c + 4 * i + 2] << 16 | data[0x15c + 4 * i + 3] << 24
	if not offset:
		continue

	len = data[offset] | data[offset + 1] << 8

	sectorlen = len * 8

	# G64 files built by tools might not contain the tail gap data,
	# so if there is significantly less data on the track than we expect,
	# don't scale it to 360 degrees, but leave the tail area empty.
	sector_capacity = 200000 / [32, 30, 28, 26][speed] * 8
	if float(sectorlen) / sector_capacity > .993:
		sector_capacity = sectorlen

	print "track {}, offset {}, size {}, speed {}, capacity {}".format(trackno, offset, len, speed, sector_capacity / 8)

	one_bits = 0
	is_sync = False
	is_header = False

	for i in range(0, len):
		byte = data[offset + i + 2]

		for j in range(0, 8):
			bit = ((byte << j) & 0x80) >> 7
			if bit > 0:
				one_bits += 1
				if one_bits >= 10:
					is_sync = True;
			else:
				one_bits = 0
				if is_sync:
					if is_header:
						x = 200
					else:
						y += 1
						x = 0
					is_header = not is_header
				is_sync = False;

			if is_sync:
				value = (0xff, 0, 0) # red
			else:
				pixel = bit * 255
				if is_header:
					value = (0, 0, pixel) # shades of blue
				else:
					value = (0, pixel, 0) # shades of green
				x += 1

#			print x,y
			pixels[x, y] = value

#img = img.resize((size / 4, size / 4), Image.ANTIALIAS)
#img = img.resize((size / 16, size / 16), Image.ANTIALIAS)
img.save(filename_out)
