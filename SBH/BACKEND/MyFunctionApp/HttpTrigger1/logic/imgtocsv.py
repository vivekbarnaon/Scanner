# !pip install python-dotenv
import google.generativeai as genai
import os
import logging
from dotenv import load_dotenv

def initialize_gemini_model():
    """Initialize the Gemini model with API key from environment variables"""
    try:
        load_dotenv()
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logging.warning(" GEMINI_API_KEY not found in environment variables")
            raise ValueError("GEMINI_API_KEY environment variable is required")
            
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-2.0-flash')
    except Exception as e:
        logging.error(f" Failed to initialize Gemini model: {str(e)}")
        raise

def load_image_data(image_path):
    """Load image data from file path"""
    if not os.path.exists(image_path):
        logging.error(f" Image file not found at {image_path}")
        raise FileNotFoundError(f"Image file not found at {image_path}")
    
    try:
        with open(image_path, "rb") as file:
            return file.read()
    except Exception as e:
        logging.error(f" Failed to read image file: {str(e)}")
        raise

def generate_csv_from_image(model, image_data, prompt=None):
    """Generate CSV data from image using Gemini model"""
    default_prompt = "Convert this image table to CSV format. Only output the raw CSV data without any markdown formatting or additional text."
    try:
        response = model.generate_content([
            prompt or default_prompt,
            {"mime_type": "image/jpeg", "data": image_data}
        ])
        return validate_and_clean_response(response.text)
    except genai.types.GenerativeError as e:
        logging.error(f" API Error: {str(e)}")
        raise RuntimeError(f"API Error: {str(e)}") from e
    except Exception as e:
        logging.error(f" Unexpected error: {str(e)}")
        raise

def validate_and_clean_response(raw_response):
    """Validate and clean the API response"""
    if not raw_response:
        logging.error(" Empty response from API")
        raise ValueError("Empty response from API")
    
    cleaned = raw_response.replace("```csv", "").replace("```", "").strip()
    logging.info(f" Successfully processed response ({len(cleaned)} chars)")
    return cleaned

def save_output(data, output_path):
    """Save CSV data to output file"""
    if not data:
        logging.error(" No data to save")
        raise ValueError("No data to save")
    
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as file:
            file.write(data)
        logging.info(f" Saved output to {output_path}")
        return output_path
    except Exception as e:
        logging.error(f" Failed to save output: {str(e)}")
        raise

def image_to_csv_pipeline(image_path, output_path="output.csv"):
    """Main pipeline to convert image to CSV"""
    logging.info(f" Starting image to CSV conversion: {image_path} -> {output_path}")
    try:
        model = initialize_gemini_model()
        image_data = load_image_data(image_path)
        csv_data = generate_csv_from_image(model, image_data)
        return save_output(csv_data, output_path)
    except Exception as e:
        logging.error(f" Pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        result_path = image_to_csv_pipeline(
            image_path="test_image.jpg",
            output_path="output/test_output.csv"
        )
        print(f"Successfully generated CSV at: {result_path}")
    except Exception as e:
        print(f"Processing failed: {str(e)}")