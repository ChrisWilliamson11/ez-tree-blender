import shutil
import os
import zipfile

def build():
    # Define paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_filename = os.path.join(base_dir, "ez-tree-blender")
    
    # We want to zip the current directory content into a folder named "ez-tree-blender" inside the zip
    # So the zip structure is:
    # ez-tree-blender/
    #   __init__.py
    #   ...
    
    # Files/Dirs to ignore
    ignore_patterns = shutil.ignore_patterns("__pycache__", "*.pyc", ".git", ".gitignore", "build.py", "*.zip", ".vscode", ".idea")
    
    # Create a temp directory for staging
    build_dir = os.path.join(base_dir, "build_temp")
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    
    addon_dir = os.path.join(build_dir, "ez-tree-blender")
    
    print(f"Copying files to {addon_dir}...")
    shutil.copytree(base_dir, addon_dir, ignore=ignore_patterns)
    
    print(f"Creating zip archive {output_filename}.zip...")
    shutil.make_archive(output_filename, 'zip', build_dir)
    
    print("Cleaning up...")
    shutil.rmtree(build_dir)
    
    print(f"Build complete: {output_filename}.zip")

if __name__ == "__main__":
    build()
