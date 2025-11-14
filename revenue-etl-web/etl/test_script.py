#!/usr/bin/env python3
"""
Test ETL Script
Simple script for testing the ETL runner
"""

import time
import sys

print("Test ETL Script started")
print("Processing data...")

for i in range(1, 6):
    print(f"Step {i}/5: Processing...")
    time.sleep(0.5)

print("Data processing complete!")
print("Generating report...")
time.sleep(0.5)

print("Report generated successfully!")
print("Test ETL Script completed")

sys.exit(0)
