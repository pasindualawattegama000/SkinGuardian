import os
import shutil
import random

# Set the path to the Dermnet dataset
dataset_path = "C:/Users/pasin/Documents/IIT/FYP/Skin Cancer Detection cnn/DERMNET/archive/train"




# Set the path where you want to create the new folders
output_path = "C:/Users/pasin/Documents/IIT/FYP/Skin Cancer Detection cnn/DERMNET/archive/random 100"

# Iterate through each folder in the dataset
for disease_folder in os.listdir(dataset_path):
    disease_folder_path = os.path.join(dataset_path, disease_folder)

    # Create a new folder for each skin disease in the output path
    output_disease_folder = os.path.join(output_path, disease_folder)
    os.makedirs(output_disease_folder, exist_ok=True)
    # Get a list of all images in the current disease folder
    images = [img for img in os.listdir(disease_folder_path) if img.endswith('.jpg')]
    # Select random 100 images (or less if there are fewer than 100)
    selected_images = random.sample(images, min(50, len(images)))

    # Copy the selected images to the new folder
    for img in selected_images:
        src_path = os.path.join(disease_folder_path, img)
        dest_path = os.path.join(output_disease_folder, img)
        shutil.copy(src_path, dest_path)

print("Task completed successfully.")
