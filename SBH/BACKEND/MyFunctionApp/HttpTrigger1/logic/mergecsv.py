#!pip install pandas google-generativeai
# Run this cell first to install required packages
#!pip install -q google-generativeai pandas python-dotenv ipython
# import os
# os.environ["GOOGLE_API_KEY"] = "AIzaSyDEYkoLR5ESvf1h1hetea8p8ILPxBKVL2Q"



import os
import pandas as pd
import json
import shutil
import re
import google.generativeai as genai
import logging

class CSVMatcher:
    def __init__(self, data_dir="data", output_dir="output"):
        self.data_dir = data_dir
        self.output_dir = output_dir
        self.csv_data_dict = {}
        self.ensure_directories()
        self.load_dictionary()

        # Get API key from environment variables
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logging.warning(" GEMINI_API_KEY not found in environment variables")
            api_key = "AIzaSyDEYkoLR5ESvf1h1hetea8p8ILPxBKVL2Q"  # Fallback for testing
            
        genai.configure(api_key=api_key)
        self.gemini_model = genai.GenerativeModel("gemini-2.0-flash")

    def ensure_directories(self):
        """Create folders if they don't exist"""
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

    def load_all_csvs(self):
        """Scan all CSV files from the data folder"""
        csv_files = [f for f in os.listdir(self.data_dir) if f.endswith('.csv')]
        if not csv_files:
            logging.warning(" No CSV file found!")
            return []

        logging.info(f" Found {len(csv_files)} CSV files")
        results = []
        for file in csv_files:
            file_path = os.path.join(self.data_dir, file)
            try:
                df = pd.read_csv(file_path)
                if df.empty or len(df.columns) < 1:
                    logging.warning(f" {file} - Empty/Invalid file")
                    continue
                result = self.analyze_csv(file, df)
                if result:
                    results.append(result)
            except Exception as e:
                logging.error(f" {file} could not be analyzed: {str(e)}")
        
        return results

    def analyze_csv(self, filename, df):
        """Analyze using Gemini and parse JSON"""
        sample = df.head(20) if len(df) >= 20 else df

        prompt = """Analyze the CSV data and return only JSON:
        {"column": "most_common_column", "value": "most_common_value"}
        No extra text!"""

        try:
            response = self.gemini_model.generate_content(f"Data: {sample.to_csv()}\n{prompt}")
            raw_response = response.text.strip()

            # Logic to extract JSON
            json_str = re.sub(r'[\s\S]*?(\{.*\})[\s\S]*', r'\1', raw_response, flags=re.DOTALL)
            json_str = json_str.replace("'", '"').replace("\\n", "").strip('`')

            # JSON validation
            data = json.loads(json_str)
            if "column" not in data or "value" not in data:
                raise ValueError("Invalid JSON format")

            col = data["column"].strip()
            val = str(data["value"]).strip()

            self.csv_data_dict[filename] = (col, val)
            self.save_dictionary()
            logging.info(f" {filename} analyzed: {col} = {val}")
            return {"file": filename, "column": col, "value": val}

        except Exception as e:
            logging.error(f" {filename} could not be analyzed: {str(e)}")
            return None

    def match_input_csv(self, input_path):
        """Process a new CSV"""
        try:
            input_path = os.path.normpath(input_path)
            if not os.path.exists(input_path):
                raise FileNotFoundError(f" File not found: {input_path}")

            file_name = os.path.basename(input_path)

            # Handle duplicates - in Azure Function we always overwrite
            if file_name in self.csv_data_dict:
                logging.info(f" {file_name} already exists! Overwriting.")
                del self.csv_data_dict[file_name]

            # Analyze the new file
            df = pd.read_csv(input_path)
            if df.empty:
                raise ValueError(" File is empty")

            result = self.analyze_csv(file_name, df)
            if not result:
                return []

            # Find matches
            current_col, current_val = self.csv_data_dict[file_name]
            matches = [
                f for f, (col, val) in self.csv_data_dict.items()
                if f != file_name
                and col.lower() == current_col.lower()
            ]

            # Merge/Add logic
            merged_files = []
            if matches:
                logging.info(f" Found {len(matches)} matches")
                for match in matches:
                    logging.info(f" Merge with {match}")
                    merged_file = self.merge_files(input_path, match)
                    if merged_file:
                        merged_files.append(merged_file)
            else:
                shutil.copy(input_path, os.path.join(self.data_dir, file_name))
                logging.info(" New entry added")
            
            return merged_files

        except Exception as e:
            logging.error(f" Error: {str(e)}")
            raise

    def merge_files(self, new_file, existing_file_name):
        """Merge CSV files"""
        try:
            new_df = pd.read_csv(new_file)
            existing_path = os.path.join(self.data_dir, existing_file_name)
            existing_df = pd.read_csv(existing_path)

            merged_name = f"merged_{existing_file_name}"
            merged_path = os.path.join(self.output_dir, merged_name)

            # Remove duplicates
            combined = pd.concat([existing_df, new_df]).drop_duplicates(keep='last')
            combined.to_csv(merged_path, index=False)
            logging.info(f" New file created: {merged_path}")

            # Add merged file to database
            self.analyze_csv(merged_name, combined)
            return merged_path

        except Exception as e:
            logging.error(f" Merge failed: {str(e)}")
            return None

    def save_dictionary(self):
        """Save data"""
        with open(os.path.join(self.output_dir, "matches.json"), 'w') as f:
            json.dump(self.csv_data_dict, f, indent=2)

    def load_dictionary(self):
        """Load saved data"""
        dict_file = os.path.join(self.output_dir, "matches.json")
        if os.path.exists(dict_file):
            try:
                with open(dict_file, 'r') as f:
                    self.csv_data_dict = json.load(f)
                logging.info(f" Loaded {len(self.csv_data_dict)} entries")
            except:
                logging.error(" JSON could not be loaded")

# Command-line interface - only used when running this file directly
def main():
    """Main program"""
    matcher = CSVMatcher()
    while True:
        print("\n" + "=" * 40)
        print("1. Analyze all CSVs")
        print("2. Add a new CSV")
        print("3. View matches")
        print("4. Exit")
        choice = input("Choose (1-4): ").strip()

        if choice == '1':
            matcher.load_all_csvs()
        elif choice == '2':
            path = input("CSV file path: ").strip()
            matcher.match_input_csv(path)
        elif choice == '3':
            print("\nCurrent matches:")
            print(json.dumps(matcher.csv_data_dict, indent=2))
        elif choice == '4':
            print(" Goodbye!")
            break
        else:
            print(" Invalid option!")

if __name__ == "__main__":
    main()
