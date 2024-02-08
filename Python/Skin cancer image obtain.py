import os
import pandas as pd
import shutil


csv_path = "C:/Users/pasin/Documents/IIT/FYP/Skin Cancer Detection cnn/HAM1000/archive (2)/HAM10000_metadata.csv"
image_folder = "C:/Users/pasin/Documents/IIT/FYP/Skin Cancer Detection cnn/HAM1000/archive (2)/HAM10000_images_part_1 + 2"
output_single_folder = "C:/Users/pasin/Documents/IIT/FYP/Skin Cancer Detection cnn/HAM1000/archive (2)/140 selected images"

# Load the CSV file into a Pandas DataFrame
df = pd.read_csv(csv_path)
os.makedirs(output_single_folder, exist_ok=True)

images_per_cancer_type = 140
# Iterate through each unique cancer type in the "dx" column
for cancer_type in df['dx'].unique():
    # Filter the DataFrame for the current cancer type
    cancer_type_df = df[df['dx'] == cancer_type]
    # Get the first 140 images for the current cancer type
    selected_images = cancer_type_df['image_id'].head(images_per_cancer_type).tolist()

    # Copy the selected images to the new single folder
    for img in selected_images:
        src_path = os.path.join(image_folder, img + '.jpg')
        dest_path = os.path.join(output_single_folder, img + '.jpg')
        shutil.copy(src_path, dest_path)

print("Task completed successfully.")
