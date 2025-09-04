import cadquery as cq
import os
import zipfile
def import_step_files(directory):
    step_parts = []

    # Load all .step files in the directory
    for filename in os.listdir(directory):
        if filename.endswith('.step'):
            file_path = os.path.join(directory, filename)
            part = cq.importers.importStep(file_path)

            # Check if the part imported successfully
            if part is not None:
                step_parts.append(part)
            else:
                print(f"Warning: {filename} could not be loaded and was skipped.")

    return step_parts

def create_compound(components: list[cq.Solid]) -> cq.Compound:
    """
    Create a CadQuery Compound object from a list of CadQuery Solid objects.

    This function takes a list of CadQuery Solid objects, extracts the underlying geometric values
    from each Solid, and combines them into a single Compound object.

    Args:
        components (list[cq.Solid]): List of CadQuery Solid objects.

    Returns:
        cq.Compound: CadQuery Compound object
        containing the combined geometric values of all input Solids.
    """
    vals = []
    for component in components:
        for sub_solid in component.all():
            vals.extend(sub_solid.vals())
        compound_object = cq.Compound.makeCompound(vals)
    return compound_object
# Directory containing your .step files
# Unzip 'zipped_cad.zip' to 'stell_cad'
zip_file = 'zipped_cad.zip'  # Replace with the correct path to your zip file if necessary
directory = 'stell_cad'      # Directory to extract to

# Ensure the output directory exists
os.makedirs(directory, exist_ok=True)

with zipfile.ZipFile(zip_file, 'r') as zip_ref:
    zip_ref.extractall(directory)

step_parts = import_step_files(directory)
compound = create_compound(step_parts)
cq.exporters.export(compound, 'combined_coils.step')