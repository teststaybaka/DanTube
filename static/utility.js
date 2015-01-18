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