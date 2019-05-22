import sys, math
from PIL import Image, ImageDraw

verbose = False

sizex = 3000
sizey = 927

def get_8_bits(data, offset):
	byte_offset = offset / 8
	bit_offset = offset % 8
	byte = data[byte_offset]
	next_byte = data[byte_offset + 1]
	byte_part = (byte & (((1 << (8 - bit_offset)) - 1))) << bit_offset
	byte_part_2 = next_byte >> (8 - bit_offset)
	return byte_part | byte_part_2

def get_5_bits(data, offset):
	return get_8_bits(data, offset) >> 3

def de_gcr(a):
	gcr_code = [
		0b01010,
		0b01011,
		0b10010,
		0b10011,
		0b01110,
		0b01111,
		0b10110,
		0b10111,
		0b01001,
		0b11001,
		0b11010,
		0b11011,
		0b01101,
		0b11101,
		0b11110,
		0b10101
	]
	if not a in gcr_code:
		return -1
	return gcr_code.index(a)

def de_gcr_byte(data, offset):
	hi = de_gcr(get_5_bits(data, offset))
	lo = de_gcr(get_5_bits(data, offset + 5))
	if hi == -1 or lo == -1:
		return -1
	return  hi << 4 | lo

def speed_for_track(track):
	if track < 18:
		return 3
	if track < 25:
		return 2
	if track < 31:
		return 1
	return 0

def sectors_for_track(track):
	return [17, 18, 19, 21][speed_for_track(track)]

def sector_offset_for_track(track):
	ret = 0
	for i in range(1, track):
		ret += sectors_for_track(i)
	return ret

def y_for_track_sector(track, sector):
	if sector >= sectors_for_track(track) or sector < 0:
		return sizey
	return sector_offset_for_track(track) + 3 * (track - 1) + sector

filename_in = sys.argv[1]
filename_out = sys.argv[2]

data = bytearray(open(filename_in, 'rb').read())

signature = data[:8]
version = data[8]
notracks = data[9]
tracksize = data[10] | data[11] << 8

img = Image.new('RGB', (sizex, sizey), color = 'white')
pixels = img.load()
draw = ImageDraw.Draw(img)

# draw outside = don't draw
x = sizex
y = sizey

for i in range(0, notracks):
	trackno = i / 2 + 1

	track_y = y_for_track_sector(trackno, 0)
	draw.line((0, track_y - 2, sizex - 1, track_y - 2), fill = (0xc0, 0xc0, 0xc0), width = 1)
	draw.text((5, track_y), str(trackno), fill=(0, 0, 0))

	offset = data[12 + 4 * i] | data[12 + 4 * i + 1] << 8 | data[12 + 4 * i + 2] << 16 | data[12 + 4 * i + 3] << 24
	speed = data[0x15c + 4 * i] | data[0x15c + 4 * i + 1] << 8 | data[0x15c + 4 * i + 2] << 16 | data[0x15c + 4 * i + 3] << 24
	if not offset:
		continue

	len = data[offset] | data[offset + 1] << 8

	sectorlen = len * 8

	print "track {}, offset {}, size {}, speed {}".format(trackno, offset, len, speed)

	is_sync = False
	is_header = False
	last_sync = 0
	before_first_sync = True

	track_data = data[offset + 2:]

	sector = -1

	for i in range(0, len):
		byte = track_data[i]

		for j in range(0, 8):
			bit = ((byte << j) & 0x80) >> 7
			data2 = track_data[i:]
			if get_5_bits(data2, j) == 0x1F and get_5_bits(data2, j + 5) == 0x1F:
				is_sync = True

			if is_sync and bit == 0:
				is_sync = False;

				was_short_data = not before_first_sync and not is_header and  i - last_sync < 320
				if was_short_data:
					print "Warning: Sector {}: short data: {} bytes".format(sector, i - last_sync)
				before_first_sync = False

				last_sync = i
				header_data = track_data[i:]
				code = de_gcr_byte(header_data, j)
				if code == 8: # header
					checksum = de_gcr_byte(header_data, j + 10)
					sector = de_gcr_byte(header_data, j + 20)
					track = de_gcr_byte(header_data, j + 30)
					is_header = True
					y = y_for_track_sector(trackno, sector)
					if verbose:
						print "header", track, sector
					x = 20
				elif code == 7: # data
					if is_header:
						is_header = False
					else:
						if was_short_data:
							# Common error: The drive wrote the sector too late,
							# so the original SYNC and ~28 GCR bytes are still intact,
							# but aborted, followed by the newly written SYNC and
							# the new data. We will ignore the aborted sector and
							# assume the data after the SYNC is the correct version
							# of the same sector.
							# Note that this error probably also means that the next
							# sector's header is missing (which we can recover from),
							# and maybe even the SYNC of the next data block is missing
							# (which we can't recover from).
							print "Warning: No header, but short data! Assuming repeated sector {}".format(sector)
						else:
							sector += 1
							if sector > sectors_for_track(trackno):
								sectors = 0
							print "Warning: No header! Assuming sector {}".format(sector)
					y = y_for_track_sector(trackno, sector)
					if verbose:
						print "data  ", trackno, sector
					x = 190
				else:
					print "Warning: Code {}".format(code)
					checksum = de_gcr_byte(header_data, j + 10)
					sector = de_gcr_byte(header_data, j + 20)
					track = de_gcr_byte(header_data, j + 30)
					y = sizey
				if sector >= sectors_for_track(trackno):
					print "Warning: Extra sector {}".format(sector)


			if not is_sync:
				pixel = bit * 255
				if is_header:
					value = (0, pixel, pixel) # shades of blue
				else:
					value = (0, pixel, 0) # shades of green
				if x < sizex and y < sizey:
					pixels[x, y] = value
				x += 1

	y += 1

#img = img.resize((size / 4, size / 4), Image.ANTIALIAS)
#img = img.resize((size / 16, size / 16), Image.ANTIALIAS)
img.save(filename_out)
