
// paste this text in process > batch > macro window to process a whole folder

title = getTitle();

// use registration_channel=1 to register using 1st channel as the reference
run("Linear Stack Alignment with SIFT MultiChannel", "registration_channel=1 initial_gaussian_blur=1.60 steps_per_scale_octave=3 minimum_image_size=64 maximum_image_size=1024 feature_descriptor_size=4 feature_descriptor_orientation_bins=8 closest/next_closest_ratio=0.92 maximal_alignment_error=100 inlier_ratio=0.05 expected_transformation=Rigid interpolate");

selectImage(title);
close();
selectImage("Aligned_"+title);
rename(title);
