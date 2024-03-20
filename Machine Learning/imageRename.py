import os

folder_path = "C:/Users/pasin/Desktop/IIT/FYP/Skin Cancer Detection cnn/Dataset/Non cancer"
file_extension = ".JPG"  # Update the file extension based on your image format
prefix = "image"

counter = 42
for filename in os.listdir(folder_path):
    if filename.endswith(file_extension) or filename.endswith(file_extension):
        new_filename = prefix + str(counter) + file_extension
        os.rename(os.path.join(folder_path, filename),
                  os.path.join(folder_path, new_filename))
        counter += 1
