#!pip install gmft PyPDFium2 pandas
#!pip list | grep gmft

import os
import gmft
import gmft.table_detection
import gmft.table_visualization
import gmft.table_function
import gmft.algorithm.structure
import gmft.pdf_bindings.bindings_pdfium
import gmft.pdf_bindings
import gmft.common
import pandas as pd

from gmft.pdf_bindings import PyPDFium2Document
from gmft import CroppedTable, TableDetector, AutoTableFormatter, AutoFormatConfig
from gmft.algorithm.structure import *

detector = TableDetector()

def pdf_to_csv(source_path, output_dir="output"):
    """
    Extract tables from PDF and convert them to CSV files
    
    Args:
        source_path: Path to the PDF file
        output_dir: Directory to save the CSV files
        
    Returns:
        List of paths to the generated CSV files
    """
    print(f"Processing PDF: {source_path}")
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Open the PDF document
    doc = PyPDFium2Document(source_path)
    tables = []
    for page in doc:
        tables += detector.extract(page)

    filtered_tables = [item for item in tables if item.confidence_score < 1]
    output_files = []

    for i, table in enumerate(filtered_tables):
        formatter = AutoTableFormatter()
        formatter.config = AutoFormatConfig()
        formatted_table = formatter.extract(table)
        
        # Get dataframe and save to CSV
        df = formatted_table.df().fillna("")
        csv_filename = os.path.join(output_dir, f"table_{i}.csv")
        df.to_csv(csv_filename, index=False)
        output_files.append(csv_filename)
        print(f"CSV File Generated: {csv_filename}")
    
    return output_files

# Remove the test code that was intended for Jupyter/Colab
# pdf_path = "/content/multiple_tables_sample.pdf"
# pdf_to_csv(pdf_path)
