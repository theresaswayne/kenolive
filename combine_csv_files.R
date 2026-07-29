# combine_csv_files.R
# merges a batch of csv files, putting the filename in a new column
# Requirement: All files must be within a single folder and the name must contain the pattern noted in line 20
# adapted from http://serialmentor.com/blog/2016/6/13/reading-and-combining-many-tidy-data-files-in-R

# Setup -------
require(tidyverse)

# text to filter for in the end of the file name
finalText <- "C2_Results.csv"

# ---- Prompt for a data folder ----
# no message will be displayed. Choose one of the files in the folder
selectedFile <- file.choose()
inputFolder <- dirname(selectedFile) # the input is the parent of the selected file

# Read all the files in the folder ------

outputFolder <- dirname(inputFolder) # parent of the input folder

# get file names
files <- dir(inputFolder, pattern = paste("*",finalText,sep=""))

# tibble is used because of the warning that data_frame is deprecated.
mergedDataWithNames <- tibble(filename = files) %>% # tibble holding file names
  mutate(file_contents =
           map(filename,          # read files into a new data column
               ~ read_csv(file.path(inputFolder, .),
                          locale = locale(encoding = "latin1"),
                          na = c("", "N/A"))))

# unnest to make the list into a flat file again,
# but it now has 1 extra column to hold the filename
mergedDataFlat <- unnest(mergedDataWithNames, cols = c(file_contents))


# Write an output file of all the merged data ----------

outputFile = paste(basename(inputFolder), "_merged_", finalText, sep = "")
write_csv(mergedDataFlat,file.path(outputFolder, outputFile))

