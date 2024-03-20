import os
import shutil

# Set the path to the folder containing subfolders of each skin disease
input_path = 'C:/Users/pasin/Documents/IIT/FYP/Skin Cancer Detection cnn/DERMNET/archive/random 100 only Skin Disease'

# Set the path where you want to create the new single folder
output_single_folder = "C:/Users/pasin/Documents/IIT/FYP/Skin Cancer Detection cnn/DERMNET/archive/All Skin Diseases"

# Create the output folder if it doesn't exist
os.makedirs(output_single_folder, exist_ok=True)

# Iterate through each subfolder in the input path
for disease_folder in os.listdir(input_path):
    disease_folder_path = os.path.join(input_path, disease_folder)

    # Get a list of all images in the current disease folder
    images = [img for img in os.listdir(disease_folder_path) if img.endswith('.jpg')]

    # Copy the images to the new single folder
    for img in images:
        src_path = os.path.join(disease_folder_path, img)
        dest_path = os.path.join(output_single_folder, img)
        shutil.copy(src_path, dest_path)

print("Task completed successfully.")
