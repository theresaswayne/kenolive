# commands to process intensity data

# ---- Setup ----
require(tidyverse)
require(ggplot2)

dataName = "260717"

# assumes we have 2 dataframes, C1 and C2, derived from ImageJ measurements

# rename dummy "...1" column (ImageJ does not provide a header)
C1_mod <- rename(C1, "Measurement" = `...2`) # may be ...1 if only a single dataset is used
C2_mod <- rename(C2, "Measurement" = `...2`)

# remove the channel columns
C1_mod <- C1_mod %>% select(-Ch)
C2_mod <- C2_mod %>% select(-Ch)

#   rename data columns that are specific to each channel
C1_mod <- rename_with(C1_mod, 
                             ~ paste0("C1_", .x),
                             any_of(c("Mean", 
                                      "IntDen",
                                      "RawIntDen")))

C2_mod <- rename_with(C2_mod, 
                      ~ paste0("C2_", .x),
                      any_of(c("Mean", 
                               "IntDen",
                               "RawIntDen")))

# join by the Label column, keeping the specific Means, and a single centroid and area
joined <- left_join(C1_mod, C2_mod, by=join_by(Label, Area, X, Y, Frame, Measurement))

# save the result
# generate filename from image name
outputName = paste(dataName,"measurements.csv", sep = "_")
# write CSV file
write_csv(joined,outputName)