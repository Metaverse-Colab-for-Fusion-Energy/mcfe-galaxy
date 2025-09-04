import zipfile
import os
# Find and zip all STEP files
zip_filename = "rad_build.zip"
with zipfile.ZipFile(zip_filename, "w") as rad_zip:
    for file in os.listdir(os.getcwd()):
        if file.endswith(".step"):
            rad_zip.write(file)
            print(f"Added {file} to {zip_filename}")

print(f"Zipped all .step files into {zip_filename}")
