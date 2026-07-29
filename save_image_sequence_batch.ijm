//@File(label = "Input directory", style = "directory") inputDir
//@File(label = "Output directory", style = "directory") outputDir
//@String (label = "File suffix", value = ".tif") fileSuffix
//@ int(label="Some numerical parameter:")  numericalParameter

// save_image_sequence_batch.ijm
// ImageJ/Fiji script to save a batch of images as individual images
// Note: All images are saved in the same directory
// Theresa Swayne, 2026
//  -------- Suggested text for acknowledgement -----------
//   "These studies used the Confocal and Specialized Microscopy Shared Resource 
//   of the Herbert Irving Comprehensive Cancer Center at Columbia University, 
//   funded in part through the NIH/NCI Cancer Center Support Grant P30CA013696."

// TO USE: Place all input images in the input folder.
// 	Create a folder for the output files. 
// 	Place your desired processing steps in the processFile function.
// 	Collect any desired parameters in the script parameters at the top. 
//		See ImageJ wiki for more script parameter options.
//		Remember to pass your parameters into the processFolder and processFile functions!
//  Run the script in Fiji. 
// 	

// ---- Setup ----

while (nImages>0) { // clean up open images
	selectImage(nImages);
	close();
}
print("\\Clear"); // clear Log window

// keep track of time
startTime = getTime();

setBatchMode(true); // faster performance
run("Bio-Formats Macro Extensions"); // support native microscope files


// ---- Run ----

print("Starting");

// Call the processFolder function, including the parameters collected at the beginning of the script

processFolder(inputDir, outputDir, fileSuffix, numericalParameter);

// Clean up images and get out of batch mode

while (nImages > 0) { // clean up open images
	selectImage(nImages);
	close(); 
}
setBatchMode(false);

time = getTime();
elapsedTime = (time - startTime)/1000;
print("Finished in ", elapsedTime , " sec");


// ---- Functions ----

function processFolder(input, output, suffix, param) {

	// this function searches for files matching the criteria and sends them to the processFile function
	filenum = -1;
	print("Processing folder", input);
	// scan folder tree to find files with correct suffix
	list = getFileList(input);
	list = Array.sort(list);
	for (i = 0; i < list.length; i++) {
		if(File.isDirectory(input + File.separator + list[i])) {
			processFolder(input + File.separator + list[i], output, suffix, param); // handles nested folders
		}
		if(endsWith(list[i], suffix)) {
			filenum = filenum + 1;
			processFile(input, output, list[i], filenum, param); // passes the filename and parameters to the processFile function
		}
	}
} // end of processFolder function


function processFile(inputFolder, outputFolder, fileName, fileNumber, parameter) {
	
	// this function processes a single image
	
	path = inputFolder + File.separator + fileName;
	print("Processing file",fileNumber," at path" ,path);	

	// determine the name of the file without extension
	dotIndex = lastIndexOf(fileName, ".");
	basename = substring(fileName, 0, dotIndex); 
	extension = substring(fileName, dotIndex);
	
	print("File basename is",basename);
	
	// open the file
	run("Bio-Formats", "open=&path");

	run("Re-order Hyperstack ...", "channels=[Channels (c)] slices=[Frames (t)] frames=[Slices (z)]");
	run("Image Sequence... ", "dir=["+outputDir+"] format=TIFF");

	
	// save the output
	//outputName = basename + "_processed.tif";
	//saveAs("tiff", outputFolder + File.separator + outputName);
	//close();
	
	// clean up
	while (nImages > 0) { // clean up open images
		selectImage(nImages);
		close(); 
	}
} // end of processFile function


	