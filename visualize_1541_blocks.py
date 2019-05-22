import sys, math
from PIL import Image, ImageDraw

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
	return gcr_code.index(a)

def de_gcr_byte(data, offset):
	return de_gcr(get_5_bits(data, offset)) << 4 | de_gcr(get_5_bits(data, offset + 5))

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
	return sector_offset_for_track(track) + 2 * (track - 1) + sector

filename_in = sys.argv[1]
filename_out = sys.argv[2]

data = bytearray(open(filename_in, 'rb').read())

signature = data[:8]
version = data[8]
notracks = data[9]
tracksize = data[10] | data[11] << 8

sizex = 3000
sizey= 750
img = Image.new('RGB', (sizex, sizey), color = 'white')
pixels = img.load()

# draw outside = don't draw
x = sizex
y = sizey

track = 0x00
sector = 0xff

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
	last_sync = 0

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
					was_short_data = not is_header and  i - last_sync < 320
					if was_short_data:
						print "Warning: Sector {}: short data: {} bytes".format(sector, i - last_sync)
					last_sync = i
					header_data = data[offset + i + 2:]
					code = de_gcr_byte(header_data, j)
					if code == 8: # header
						checksum = de_gcr_byte(header_data, j + 10)
						sector = de_gcr_byte(header_data, j + 20)
						track = de_gcr_byte(header_data, j + 30)
						is_header = True
						y = y_for_track_sector(track, sector)
#						print "header", track, sector
						x = 0
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
								if sector > sectors_for_track(track):
									sectors = 0
								print "Warning: No header! Assuming sector {}".format(sector)
						y = y_for_track_sector(track, sector)
#						print "data", track, sector
						x = 170
					else:
						print "Warning: Code {}".format(code)
						checksum = de_gcr_byte(header_data, j + 10)
						sector = de_gcr_byte(header_data, j + 20)
						track = de_gcr_byte(header_data, j + 30)
						y = sizey


				is_sync = False;

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
