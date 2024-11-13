import os
import shutil
import argparse
from datetime import datetime
import stat

def create_directories(base_dir):
    folders = ['Drivers-Pre', 'Drivers-Post', 'System32-Pre', 'System32-Post']
    for folder in folders:
        dir_path = os.path.join(base_dir, folder)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"Created directory: {dir_path}")

def copy_files(src, dest, extension, only_recent=False):
    if not os.path.exists(src):
        print(f"Source directory {src} does not exist.")
        return
    
    # Set the time threshold to the first day of the current month
    current_time = datetime.now()
    time_threshold = current_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    for root, dirs, files in os.walk(src):
        for file in files:
            if file.endswith(extension):
                src_file = os.path.join(root, file)
                dest_file = os.path.join(dest, file)
                
                if only_recent:
                    # Check if the file has been modified within the current month
                    src_mtime = datetime.fromtimestamp(os.path.getmtime(src_file))
                    if src_mtime < time_threshold:
                        continue

                shutil.copy2(src_file, dest_file)
                print(f"Copied {src_file} to {dest_file}")

def remove_readonly(func, path, _):
    os.chmod(path, stat.S_IWRITE)
    func(path)

def cleanup_pre_folder(pre_folder, post_folder):
    if not os.path.exists(pre_folder) or not os.path.exists(post_folder):
        print(f"Either {pre_folder} or {post_folder} does not exist.")
        return

    for root, dirs, files in os.walk(pre_folder):
        for file in files:
            pre_file = os.path.join(root, file)
            post_file = os.path.join(post_folder, file)
            if not os.path.exists(post_file):
                try:
                    os.remove(pre_file)
                    print(f"Deleted {pre_file} as it does not exist in {post_folder}")
                except PermissionError:
                    print(f"Permission error encountered. Attempting to remove read-only attribute for {pre_file}")
                    os.chmod(pre_file, stat.S_IWRITE)
                    try:
                        os.remove(pre_file)
                        print(f"Successfully deleted {pre_file} after removing read-only attribute")
                    except Exception as e:
                        print(f"Failed to delete {pre_file}. Error: {e}")

def main(fetch_updated):
    # Get current month and year
    current_date = datetime.now()
    month_year = current_date.strftime("%B_%Y")

    # Create base directory
    base_dir = os.path.join(os.getcwd(), month_year)
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
        print(f"Created base directory: {base_dir}")

    # Step 1: Create directories
    create_directories(base_dir)
    
    # Step 2: Copy .sys files from drivers to Drivers-Pre
    if not fetch_updated:
        print("Copying .sys files to Drivers-Pre")
        copy_files(r'C:\Windows\System32\drivers', os.path.join(base_dir, 'Drivers-Pre'), '.sys')
        
    # Step 3: Copy .dll files from System32 to System32-Pre
    if not fetch_updated:
        print("Copying .dll files to System32-Pre")
        copy_files(r'C:\Windows\System32', os.path.join(base_dir, 'System32-Pre'), '.dll')
    
    # Step 4: If --fetch-updated is provided, copy recently modified files to Drivers-Post and System32-Post
    if fetch_updated:
        print("Copying recently modified .sys files to Drivers-Post")
        copy_files(r'C:\Windows\System32\drivers', os.path.join(base_dir, 'Drivers-Post'), '.sys', only_recent=True)
        print("Copying recently modified .dll files to System32-Post")
        copy_files(r'C:\Windows\System32', os.path.join(base_dir, 'System32-Post'), '.dll', only_recent=True)
        
        # Step 5: Cleanup Pre folders by deleting files that don't exist in Post folders
        print("Cleaning up Drivers-Pre")
        cleanup_pre_folder(os.path.join(base_dir, 'Drivers-Pre'), os.path.join(base_dir, 'Drivers-Post'))
        print("Cleaning up System32-Pre")
        cleanup_pre_folder(os.path.join(base_dir, 'System32-Pre'), os.path.join(base_dir, 'System32-Post'))

if __name__ == "__main__":
    """Very simple but effective script for patch tuesdays
        1. Run it before the update to get files for diff
        2. Run it after the update to get files that have been updated and cleanup the rest
        3. Now the fun begins :)
    """
    parser = argparse.ArgumentParser(description='Copy system files for analysis.')
    parser.add_argument('--fetch-updated', action='store_true', help='Copy only recently modified files to Drivers-Post and System32-Post.')
    
    args = parser.parse_args()
    main(args.fetch_updated)
