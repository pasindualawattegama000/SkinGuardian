import os
import pandas as pd
from shutil import copyfile

images_directory = r"C:\Users\pasin\Documents\IIT\FYP\Skin Cancer Detection cnn\HAM1000\archive (2)\HAM10000_images_part_1 + 2"
csv_file_path = r"C:\Users\pasin\Documents\IIT\FYP\Skin Cancer Detection cnn\HAM1000\archive (2)\HAM10000_metadata.csv"
output_directory = r"C:\Users\pasin\Documents\IIT\FYP\Skin Cancer Detection cnn\2024 Train\HAM10000 Organized"

# Read the CSV file
metadata = pd.read_csv(csv_file_path)

# Loop through the dataframe and organize images
for index, row in metadata.iterrows():
    image_id = row['image_id']
    diagnosis = row['dx']

    diagnosis_directory = os.path.join(output_directory, diagnosis)
    source_path = os.path.join(images_directory, f'{image_id}.jpg')
    destination_path = os.path.join(diagnosis_directory, f'{image_id}.jpg')

    # Copy the image to the new directory
    copyfile(source_path, destination_path)



