

function load_binary_resource(url)
{
	var byteArray = [];
	var req = new XMLHttpRequest();
	req.open('GET', url, false);
	req.overrideMimeType('text\/plain; charset=x-user-defined');
	req.send(null);
	if (req.status != 200) return byteArray;
	for (var i = 0; i < req.responseText.length; ++i) {
		byteArray.push(req.responseText.charCodeAt(i) & 0xff)
	}
	return byteArray;
}

function bin2String(array, start, end)
{
	var result = "";
	for (var i = start; i <= end; i++) {
	  result += String.fromCharCode(parseInt(array[i], 2));
	}
	return result;
}


function renderImage(source_url)
{
	data = load_binary_resource(source_url);
	filename = source_url.toString().match(/.*\/(.+?)$/)[1];
	console.log(filename);

	signature = bin2String(data, 0, 7);
	version = data[8];
	notracks = data[9];
	tracksize = data[10] | data[11] << 8;

	var width = window.innerWidth;
	var height = window.innerHeight;
	var size = 11000;

	var canvas = document.createElement('canvas');
	canvas.width  = size;
	canvas.height = size;

	var context = canvas.getContext("2d");

	track_distance = size / 150;

	/// conversion factor for scale, we want 300 DPI in this example
	var dpiFactor = 300 / 96, size, size;

	/// scale all sizes incl. font size
	context.font = (100 * dpiFactor).toFixed(0) + 'px sans-serif';

	/// scale all positions
	context.fillText(filename, 100, 250);

	console.log("signature: " + signature + ", version: " + version + ", notracks: " + notracks + ", tracksize: " + tracksize + ", track_distance: " + track_distance);

	for (i=0; i<notracks; i++)
	{
		trackno = i / 2 + 1;
		offset = data[12 + 4 * i] | data[12 + 4 * i + 1] << 8 | data[12 + 4 * i + 2] << 16 | data[12 + 4 * i + 3] << 24;
		speed = data[0x15c + 4 * i] | data[0x15c + 4 * i + 1] << 8 | data[0x15c + 4 * i + 2] << 16 | data[0x15c + 4 * i + 3] << 24;
		if (offset)
		{
			len = data[offset] | data[offset + 1] << 8;

			sectorlen = len * 8;
			radius = size * .99 / 2 - trackno * track_distance;
			radius1 = radius - track_distance / 2.1;
			radius2 = radius + track_distance / 2.1;

			// G64 files built by tools might not contain the tail gap data,
			// so if there is significantly less data on the track than we expect,
			// don't scale it to 360 degrees, but leave the tail area empty.
			sector_capacity = 200000 / [32, 30, 28, 26][speed] * 8;
			if (parseFloat(sectorlen) / sector_capacity > .993)
				sector_capacity = sectorlen;

			console.log("track " + trackno + ", offset " + offset + ", size " + len + ", speed " + speed + ", capacity " + (sector_capacity / 8));

			for (n=0; n<sectorlen; n++)
			{
				angle = parseFloat(n) / sector_capacity * 2 * Math.PI;
				x1 = parseInt(Math.round(size / 2 + radius1 * Math.sin(angle)));
				y1 = parseInt(Math.round(size / 2 + radius1 * Math.cos(angle)));
				x2 = parseInt(Math.round(size / 2 + radius2 * Math.sin(angle)));
				y2 = parseInt(Math.round(size / 2 + radius2 * Math.cos(angle)));
				byte = data[parseInt(offset + n / 8) + 2];

				if (byte == 0x00)
				{
					value = "rgb(0, 0, 255)";  // empty = blue
				}
				else if (byte == 0xff)
				{
					value = "rgb(255, 0, 0)";  // sync = red
				}
				else
				{
					pixel = ((byte >> (n % 7)) & 1) * 255;
					value = "rgb(0," + pixel + ",0)";  // shades of green
				}

				context.beginPath();
				context.moveTo(x1, y1); 
				context.lineTo(x2, y2);
				context.strokeStyle = value;
				context.lineWidth = 2;
				context.stroke();
			}
		}
	}

	console.log("Rendering disk image!");
//	var discImage = document.createElement('img');
//	discImage.src = canvas.toDataURL("image/png");
//	discImage.width  = 640;
//	discImage.height = 640;
//	document.body.appendChild(discImage);

        canvas.toBlob((blob) => {
            const discImage = document.createElement("img");
            const url = URL.createObjectURL(blob);

            discImage.onload = () => {
              // no longer need to read the blob so it's revoked
              URL.revokeObjectURL(url);
            };

            discImage.src = url;
            discImage.width = 640;
            discImage.height = 640;
            document.body.appendChild(discImage);
        });
}
