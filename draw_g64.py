import sys, math
from PIL import Image, ImageDraw

filename_in = sys.argv[1]
filename_out = sys.argv[2]

data = bytearray(open(filename_in, 'rb').read())

signature = data[:8]
version = data[8]
notracks = data[9]
tracksize = data[10] | data[11] << 8
#print signature
#print version
#print notracks
#print tracksize

size = 10000
img = Image.new('RGB', (size, size), color = 'white')
draw = ImageDraw.Draw(img)

for i in range(0, notracks):
	trackno = i / 2 + 1
	offset = data[12 + 4 * i] | data[12 + 4 * i + 1] << 8 | data[12 + 4 * i + 2] << 16 | data[12 + 4 * i + 3] << 24
	if not offset:
		continue

	len = data[offset] | data[offset + 1] << 8
	print "track {}, offset {}, size {}".format(trackno, offset, len)

	sectorlen = len * 8
	radius = size * .45 - trackno * size / 200

	for i in range(0, sectorlen):
		angle = - float(i) / sectorlen * 2 * math.pi
		x = int(round(size / 2 + radius * math.sin(angle)))
		y = int(round(size / 2 + radius * math.cos(angle)))
#		print hex(data[offset + i]),
		pixel = 255 - ((data[offset + i / 8 + 2] >> (i % 7)) & 1) * 255
		value = (pixel, pixel, pixel)
#		img.putpixel((x, y), value)
		r = 20
		draw.ellipse((x - r, y - r, x + r, y + r), fill = value)

img.save(filename_out)
