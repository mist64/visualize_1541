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

size = 5000
img = Image.new('RGB', (size, size), color = 'white')
draw = ImageDraw.Draw(img)

print '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 20010904//EN" "http://www.w3.org/TR/2001/REC-SVG-20010904/DTD/svg10.dtd">'
print '<svg width="{}" height="{}">'.format(size, size)
print '    <defs>'
print '        <linearGradient id="Gradient-1">'


for i in range(0, notracks):
	trackno = i / 2 + 1
	offset = data[12 + 4 * i] | data[12 + 4 * i + 1] << 8 | data[12 + 4 * i + 2] << 16 | data[12 + 4 * i + 3] << 24
	if not offset:
		continue

	len = data[offset] | data[offset + 1] << 8
	print "<!-- track {}, offset {}, size {} -->".format(trackno, offset, len)

	sectorlen = len * 8
	radius = size * .45 - trackno * size / 200
	radius1 = radius - 20
	radius2 = radius + 20

	for i in range(0, sectorlen / 10):
		angle = - float(i) / sectorlen * 2 * math.pi
		x1 = int(round(size / 2 + radius1 * math.sin(angle)))
		y1 = int(round(size / 2 + radius1 * math.cos(angle)))
		x2 = int(round(size / 2 + radius2 * math.sin(angle)))
		y2 = int(round(size / 2 + radius2 * math.cos(angle)))
#		print hex(data[offset + i]),
		byte = data[offset + i / 8 + 2]
		if byte == 0:
			value = (0, 0, 0xff)
		elif byte == 0xff:
			value = (0xff, 0, 0)
		else:
#			value = (byte, byte, byte)
			pixel = ((byte >> (i % 7)) & 1) * 255
			value = (0, pixel, 0)

#		img.putpixel((x, y), value)
#		r = 20
#		draw.ellipse((x - r, y - r, x + r, y + r), fill = value)
		draw.line((x1, y1, x2, y2), fill = value)
#		print '<line x1="{}" y1="{}" x2="{}" y2="{}" stroke="#333333" stroke-width="3px"></line>'.format(x1,y1,x2,y2)
		print '            <stop offset="{}%" stop-color="#{:02x}{:02x}{:02x}" />'.format(-angle / 2 / math.pi * 100, value[0], value[1], value[2])

img.save(filename_out)

print '        </linearGradient>'
print '    </defs>'
print '    <rect x="10" y="10" width="200" height="100" fill= "url(#Gradient-1)" stroke="#333333" stroke-width="3px" />'
print '</svg>'
