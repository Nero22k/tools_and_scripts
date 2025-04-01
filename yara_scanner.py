#!/usr/bin/env python3
import argparse
import os
import sys
import subprocess
import json
import concurrent.futures
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

class YaraScanner:
    def __init__(self, 
                 yara_path: str = "yara64.exe", 
                 rules_dir: str = None,
                 target_file: str = None,
                 output_format: str = "text",
                 max_workers: int = 4,
                 timeout: int = 30):
        self.yara_path = yara_path
        self.rules_dir = rules_dir
        self.target_file = target_file
        self.output_format = output_format
        self.max_workers = max_workers
        self.timeout = timeout
        self.results = []

    def find_rule_files(self) -> List[str]:
        """Find all YARA rule files in the specified directory."""
        rule_files = []
        
        if not self.rules_dir or not os.path.isdir(self.rules_dir):
            print(f"Error: Rules directory not found or not a directory: {self.rules_dir}")
            return []
        
        # Find all .yar files
        for root, _, files in os.walk(self.rules_dir):
            for file in files:
                if file.endswith(('.yar', '.yara')):
                    rule_files.append(os.path.join(root, file))
        
        print(f"Found {len(rule_files)} YARA rule files")
        return rule_files

    def scan_with_rule(self, rule_file: str) -> Dict[str, Any]:
        """
        Scan the target file with a single YARA rule file.
        
        Args:
            rule_file: Path to the YARA rule file
            
        Returns:
            Dictionary with scan results
        """
        rule_name = os.path.basename(rule_file)
        print(f"Scanning with rule: {rule_name}...")
        
        cmd = [
            self.yara_path,
            "-s",  # Print matching strings
            "-m",  # Print metadata
            "-g",  # Print tags
            rule_file,
            self.target_file
        ]
        
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=self.timeout
            )
            
            return {
                "rule_file": rule_file,
                "rule_name": rule_name,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "return_code": result.returncode,
                "matches": result.stdout.strip() != "",
                "error": result.stderr.strip() if result.stderr.strip() else None
            }
        except subprocess.TimeoutExpired:
            return {
                "rule_file": rule_file,
                "rule_name": rule_name,
                "stdout": "",
                "stderr": f"Timeout after {self.timeout} seconds",
                "return_code": -1,
                "matches": False,
                "error": f"Timeout after {self.timeout} seconds"
            }
        except Exception as e:
            return {
                "rule_file": rule_file,
                "rule_name": rule_name,
                "stdout": "",
                "stderr": str(e),
                "return_code": -1,
                "matches": False,
                "error": str(e)
            }

    def run_scan(self) -> None:
        """Run the scan with all rule files against the target file."""
        if not self.target_file or not os.path.isfile(self.target_file):
            print(f"Error: Target file not found: {self.target_file}")
            return
        
        rule_files = self.find_rule_files()
        if not rule_files:
            print("No rule files found to scan with.")
            return
        
        start_time = datetime.now()
        
        # Run scans in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_rule = {executor.submit(self.scan_with_rule, rule): rule for rule in rule_files}
            for future in concurrent.futures.as_completed(future_to_rule):
                rule = future_to_rule[future]
                try:
                    result = future.result()
                    self.results.append(result)
                except Exception as e:
                    print(f"Error processing rule {rule}: {e}")
        
        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()
        
        print(f"\nCompleted scan in {elapsed:.2f} seconds")
        
        matching_rules = [r for r in self.results if r["matches"]]
        print(f"Found {len(matching_rules)} matching rules out of {len(rule_files)} total rules")

    def output_results(self, output_file: Optional[str] = None) -> None:
        """
        Output the scan results.
        
        Args:
            output_file: Path to the output file (optional)
        """
        if self.output_format == "json":
            output_data = {
                "scan_time": datetime.now().isoformat(),
                "target_file": self.target_file,
                "rules_dir": self.rules_dir,
                "total_rules": len(self.results),
                "matching_rules": len([r for r in self.results if r["matches"]]),
                "results": self.results
            }
            
            if output_file:
                with open(output_file, 'w') as f:
                    json.dump(output_data, f, indent=2)
                print(f"Results saved to {output_file}")
            else:
                print(json.dumps(output_data, indent=2))
        else:
            # Text output
            output_lines = [
                f"YARA Scan Results",
                f"=====================================",
                f"Target File: {self.target_file}",
                f"Rules Directory: {self.rules_dir}",
                f"Scan Time: {datetime.now().isoformat()}",
                f"Total Rules: {len(self.results)}",
                f"Matching Rules: {len([r for r in self.results if r['matches']])}",
                f"=====================================\n"
            ]
            
            # Sort results - matches first
            sorted_results = sorted(self.results, key=lambda x: not x["matches"])
            
            for result in sorted_results:
                if result["matches"]:
                    output_lines.append(f"[+] MATCH: {result['rule_name']}")
                    output_lines.append(f"{result['stdout']}")
                    output_lines.append("-------------------------------------")
                else:
                    if result["error"]:
                        output_lines.append(f"[!] ERROR: {result['rule_name']} - {result['error']}")
            
            output_text = "\n".join(output_lines)
            
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(output_text)
                print(f"Results saved to {output_file}")
            else:
                print(output_text)


def main():
    parser = argparse.ArgumentParser(description="Run multiple YARA rules against a single payload")
    parser.add_argument("-r", "--rules-dir", required=True, help="Directory containing YARA rule files")
    parser.add_argument("-t", "--target", required=True, help="File to scan")
    parser.add_argument("-y", "--yara-path", default="yara64.exe", help="Path to YARA executable")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("-f", "--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("-w", "--workers", type=int, default=4, help="Maximum number of concurrent workers")
    parser.add_argument("--timeout", type=int, default=20, help="Timeout in seconds for each YARA scan")
    
    args = parser.parse_args()
    
    scanner = YaraScanner(
        yara_path=args.yara_path,
        rules_dir=args.rules_dir,
        target_file=args.target,
        output_format=args.format,
        max_workers=args.workers,
        timeout=args.timeout
    )
    
    scanner.run_scan()
    scanner.output_results(args.output)


if __name__ == "__main__":
    main()