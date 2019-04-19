# visualize_1541

`visualize_1541` is a tool that creates visualizations of the data layout on `G64` Commodore 1541 disk images.

[![](disk.png)](disk.png)


See [here](https://www.pagetable.com/?p=1070) for more examples.

## Description

* Every track starts at the bottom and is drawn counter-clockwise.
* Green represents the data. Darker areas have more 0-bits.
* Red represents a longer sequence of 1-bits.
* Blue represents a longer sequence of 0-bits.

## Usage

	python visualize_1541.py disk.g64 disk.png

## Limitations

* Because the Pillow library cannot draw antialiased lines, the tool renders the image at 16x (!) the resolution and scales it down at the end. This uses *a lot* of memory, yet there are still Moiré artifacts. Using a different image library would be a good idea.
* Red areas (SYNCs marks) show up as soon as there are 8 1-bits. SYNC detection on the 1541 requires at least 10.
* The data area shows the GCR data. An option should be added to show the GCR-decoded data.
* `nibtool` `.nbz` files are better suited as sources, the tool should be extended to support them.

## Author

Michael Steil <mist64@mac.com>, https://www.pagetable.com/