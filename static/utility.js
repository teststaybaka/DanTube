function quick_sort(array, start, end, compare) {
	if (start < end) {
		var pivotValue = array[end];
		var storeIndex = start;
		for (var i = start; i < end; i++) {
			if (compare(array[i], pivotValue)) {
				var temp = array[storeIndex];
				array[storeIndex] = array[i];
				array[i] = temp;
				storeIndex += 1;
			}
		}
		var temp = array[storeIndex];
		array[storeIndex] = array[end];
		array[end] = temp;

		quick_sort(array, start, storeIndex - 1, compare);
		quick_sort(array, storeIndex + 1, end, compare);
	}
}

function numberWithCommas(x) {
    var parts = x.toString().split(".");
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    return parts.join(".");
}

function hsl2rgb(hsl) {
	var h = hsl[0];
	var s = hsl[1];
	var l = hsl[2];

	var r, g, b;
	var c = (1 - Math.abs(2*l - 1))*s;
	h = h/60;
	var x = c*(1 - Math.abs(h%2 - 1));
	if (0 <= h && h < 1) {
		r = c;
		g = x;
		b = 0;
	} else if (1 <= h && h < 2) {
		r = x;
		g = c;
		b = 0;
	} else if (2 <= h && h < 3) {
		r = 0;
		g = c;
		b = x;
	} else if (3 <= h && h < 4) {
		r = 0;
		g = x;
		b = c;
	} else if (4 <= h && h < 5) {
		r = x;
		g = 0;
		b = c;
	} else {
		r = c;
		g = 0;
		b = x;
	}
	var m = l - c/2;
	return [Math.round((r+m)*255), Math.round((g+m)*255), Math.round((b+m)*255)];
}
