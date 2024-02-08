import os
import csv


#folder_path = "C:/Users/pasin/Documents/IIT/FYP/Skin Cancer Detection cnn/HAM1000/archive (2)/140 selected images"
#folder_path = r"C:\Users\pasin\Documents\IIT\FYP\Skin Cancer Detection cnn\DERMNET\archive\All Skin Diseases"
#folder_path = r"C:\Users\pasin\Documents\IIT\FYP\Skin Cancer Detection cnn\Normal Skin"
folder_path = r"C:\Users\pasin\Documents\IIT\FYP\Skin Cancer Detection cnn\Vitiligo new"

file_extension = ".jpg"  # Update the file extension based on your image format
# Specify the output CSV file name


#output_file = r"C:\Users\pasin\Documents\IIT\FYP\Skin Cancer Detection cnn\SkinCancer vs Diesase CSV\skinCancer.csv"
#output_file = r"C:\Users\pasin\Documents\IIT\FYP\Skin Cancer Detection cnn\SkinCancer vs Diesase CSV\skinDisease.csv"
#output_file = r"C:\Users\pasin\Documents\IIT\FYP\Skin Cancer Detection cnn\SkinCancer vs Diesase CSV\normalSkin.csv"
output_file = r"C:\Users\pasin\Documents\IIT\FYP\Skin Cancer Detection cnn\SkinCancer vs Diesase CSV\vitiligo.csv"



# Initialize an empty list to store the image names
image_names = []

# Iterate over the files in the folder
for filename in os.listdir(folder_path):
    if filename.endswith(file_extension):
        # Remove the file extension
        name_without_extension = os.path.splitext(filename)[0]
        image_names.append(name_without_extension)

# Write the image names to the CSV file
with open(output_file, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Image Names'])  # Write the header
    # Write each image name as a separate row
    writer.writerows([[name] for name in image_names])
