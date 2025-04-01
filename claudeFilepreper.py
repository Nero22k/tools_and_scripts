import os
import shutil
from pathlib import Path
from typing import List, Set, Tuple


def draw_folder_structure(directory: str) -> str:
    folder_tree = []

    def traverse(current_dir, prefix=""):
        items = sorted(os.listdir(current_dir))
        for index, item in enumerate(items):
            path = Path(current_dir) / item
            connector = "└── " if index == len(items) - 1 else "├── "
            folder_tree.append(f"{prefix}{connector}{item}")
            if path.is_dir():
                extension = "    " if index == len(items) - 1 else "│   "
                traverse(path, prefix + extension)

    traverse(directory)
    return "\n".join(folder_tree)


def copy_files(
    root_dir: str,
    output_dir: str = "result",
    ignore_folders: Set[str] = None,
    ignore_patterns: Set[str] = None,
    flatten: bool = False,
    separator: str = "_",
    draw_structure: bool = False,
) -> Tuple[List[str], List[str], str]:
    if ignore_folders is None:
        ignore_folders = set()
    if ignore_patterns is None:
        ignore_patterns = set()

    root_path = Path(root_dir)
    output_path = Path(output_dir)

    # Create the output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)

    copied_files = []
    failed_copies = []

    try:
        # Walk through directory
        for current_path, dirs, files in os.walk(root_dir):
            # Remove ignored directories
            dirs[:] = [d for d in dirs if d not in ignore_folders]

            # Process files
            for file in files:
                # Skip files matching ignore patterns
                if any(
                    file.endswith(pattern.replace("*", ""))
                    for pattern in ignore_patterns
                ):
                    continue

                # Get source path
                source_path = Path(current_path) / file
                relative_path = source_path.relative_to(root_path)

                try:
                    if flatten:
                        # Create flattened filename by joining path parts
                        path_parts = list(relative_path.parts)
                        flattened_name = separator.join(path_parts)
                        dest_path = output_path / flattened_name
                    else:
                        # Preserve directory structure
                        dest_path = output_path / relative_path
                        dest_path.parent.mkdir(parents=True, exist_ok=True)

                    # Copy the file, preserving metadata
                    shutil.copy2(source_path, dest_path)
                    copied_files.append(str(relative_path))

                except Exception as e:
                    failed_copies.append(f"{relative_path} (Error: {str(e)})")

    except Exception as e:
        print(f"Error accessing directory {root_dir}: {str(e)}")
        return [], [], ""

    folder_structure = draw_folder_structure(output_dir) if draw_structure else ""

    return copied_files, failed_copies, folder_structure


# Example usage
if __name__ == "__main__":
    import argparse

    # Set up command line arguments
    parser = argparse.ArgumentParser(description="Copy files with optional flattening and folder structure drawing")
    parser.add_argument("source_dir", help="Source directory to copy from")
    parser.add_argument(
        "--output-dir", default="result", help="Output directory (default: result)"
    )
    parser.add_argument(
        "--flatten", action="store_true", help="Flatten directory structure"
    )
    parser.add_argument(
        "--separator",
        default="_",
        help="Separator for flattened filenames (default: _)",
    )
    parser.add_argument(
        "--draw-structure", action="store_true", help="Draw the folder structure"
    )
    args = parser.parse_args()

    # Define folders and patterns to ignore
    ignore_folders = {".git", "node_modules", "__pycache__", ".next"}
    ignore_patterns = {"*.pyc", "*.log", ".DS_Store", "*.sql", "*.mjs", "*.json"}

    # Copy files
    copied, failed, folder_structure = copy_files(
        args.source_dir,
        args.output_dir,
        ignore_folders=ignore_folders,
        ignore_patterns=ignore_patterns,
        flatten=args.flatten,
        separator=args.separator,
        draw_structure=args.draw_structure,
    )

    # Print results
    print("\nSuccessfully copied files:")
    for file in copied:
        print(f"[X] {file}")

    if failed:
        print("\nFailed to copy:")
        for file in failed:
            print(f"[-] {file}")

    print(f"\nTotal files copied: {len(copied)}")
    print(f"Total files failed: {len(failed)}")
    print(f"\nFiles have been copied to: {args.output_dir}/")
    if args.flatten:
        print("Directory structure was flattened")
    if folder_structure:
        print("\nFolder structure of the output directory:")
        print(f"{args.output_dir}/")
        print(folder_structure)