import os
import csv

main_folder_path = r"C:\Users\pasin\Documents\IIT\FYP\Skin Cancer Detection cnn\2024 Train\Cancerous"
output_csv_path = r"C:\Users\pasin\Documents\IIT\FYP\Skin Cancer Detection cnn\2024 Train\skin_cancer.csv"

data = []

for root, dirs, files in os.walk(main_folder_path):
    for file in files:
        if file.lower().endswith(('.png', '.jpg', '.jpeg')):
            disease_type = os.path.basename(root)
            data.append([file, disease_type])

# Writing the collected data to a CSV file
with open(output_csv_path, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['image_id', 'dx'])
    writer.writerows(data)

