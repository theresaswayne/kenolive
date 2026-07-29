# analyze intensity over time and well

# assumes a dataframe df containing 2 channels of mean intensity data
# over multiple timepoints and multiple wells

# Assumes C1 = RFP, C2 = GFP
# Assumes each timepoint = 2 hr

# get Well from image names
well <- substr(df$Label, 0, 2) # supports only single digit numbers!

df_mod <- df %>% mutate(Well = well, .before = Label,
                        Time = (Frame-1) * 2) 

# Group by well, time
time_summary <- df_mod %>% 
  group_by(Well, Time) %>% 
  summarise(`RFP Mean` = mean(C1_Mean),
            `RFP SD` = sd(C1_Mean),
            `GFP Mean` = mean(C2_Mean),
            `GFP SD` = sd(C2_Mean),
            nCells = n())


# save the result
# generate filename from image name
outputName = paste(dataName,"population_means.csv", sep = "_")
# write CSV file
write_csv(time_summary,outputName)

# plot 

# uses loess smoothing by default, not assuming any particular function

p_RFP <- ggplot(time_summary, aes(Time, `RFP Mean`, color = Well)) +
  geom_smooth() +
  labs(title = dataName,
       x = "Time (hr)",
       y = "Mean cell intensity, RFP")
p_RFP

RFPplotName = paste0(dataName, "_RFP_plot.png")
ggsave(RFPplotName, plot = p_RFP)

p_GFP <- ggplot(time_summary, aes(Time, `GFP Mean`, color = Well)) +
  geom_smooth() +
  labs(title = dataName,
       x = "Time (hr)",
       y = "Mean cell intensity, GFP")

p_GFP
GFPplotName = paste0(dataName, "_GFP_plot.png")
ggsave(GFPplotName, plot = p_GFP)
  
