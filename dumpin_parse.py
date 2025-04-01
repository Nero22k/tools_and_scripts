import re
import sys

def parse_cfg_function_table(content):
    addresses = []
    lines = content.split("\n")
    
    for line in lines:
        # Match lines that may start with 'E' or 'S' followed by spaces, and then a hexadecimal address
        match = re.match(r"^\s*[ES]?\s*([0-9A-F]{16})\s*$", line.strip(), re.I)
        if match:
            address = match.group(1)
            addresses.append(address)
    
    return addresses

def main():
    if len(sys.argv) != 2:
        print("Usage: python dumpbin_parse.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    try:
        with open(file_path, "r") as file:
            content = file.read()
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        sys.exit(1)
    
    addresses = parse_cfg_function_table(content)
    
    output_content = "addresses = [\n"
    for address in addresses:
        output_content += "    0x" + address + ",\n"
    output_content += "]"
    
    # Save the modified content to a file
    with open("addresses_array.txt", "w") as file:
        file.write(output_content)
    
    print("Addresses saved to addresses_array.txt")

if __name__ == "__main__":
    main()