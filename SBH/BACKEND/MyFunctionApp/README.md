# Azure Function Data Processing API

This Azure Function app provides an API for processing various data formats:

1. Convert tabular images to CSV files
2. Extract tables from PDF documents as CSV files
3. Match and merge CSV files based on common columns

## API Endpoints

### Process Data

```
POST /api/processData
```

This endpoint supports three actions:

#### 1. Image to CSV Conversion

**Parameters:**
- `action`: Set to `imgtocsv`
- `image_path`: Path to the image file containing a table
- `output_file` (optional): Custom name for the output CSV file

**Example Request:**
```json
{
  "action": "imgtocsv",
  "image_path": "/path/to/table_image.jpg",
  "output_file": "converted_table.csv"
}
```

**Example Response:**
```json
{
  "result": "success",
  "output_path": "/output/converted_table.csv"
}
```

#### 2. PDF to CSV Conversion

**Parameters:**
- `action`: Set to `pdfcsv`
- `pdf_path`: Path to the PDF file containing tables

**Example Request:**
```json
{
  "action": "pdfcsv",
  "pdf_path": "/path/to/document.pdf"
}
```

**Example Response:**
```json
{
  "result": "success",
  "output_paths": [
    "/output/table_0.csv",
    "/output/table_1.csv"
  ]
}
```

#### 3. CSV Matching and Merging

**Parameters:**
- `action`: Set to `mergecsv`
- `input_path`: Path to the CSV file to analyze and potentially merge

**Example Request:**
```json
{
  "action": "mergecsv",
  "input_path": "/path/to/data.csv"
}
```

**Example Response (when matches found):**
```json
{
  "result": "success",
  "merged_files": [
    "/output/merged_existing_file.csv"
  ]
}
```

**Example Response (when no matches found):**
```json
{
  "result": "success",
  "message": "CSV analyzed but no matches found"
}
```

## Error Responses

All endpoints return standardized error responses:

```json
{
  "error": "Error message details"
}
```

Common error codes:
- 400: Missing required parameters
- 404: File not found
- 500: Server processing error

## Running Locally

1. Install dependencies: `pip install -r requirements.txt`
2. Set up environment variables:
   ```
   GEMINI_API_KEY=your_google_gemini_api_key
   ```
3. Run the function app: `func start`

## Technologies Used

- Azure Functions
- Google Generative AI (Gemini)
- GMFT (Google Machine Learning for Tables)
- pandas for data manipulation
- PyPDFium2 for PDF processing 