# GraphIndex

GraphIndex is an open-source project that provides semantic mapping of table columns to ontology terms. It enables users to map table columns to terms in an ontology, with the default ontology being `schema.org`. The project uses a vector index generated with Llama Index, which is then utilized by LLM (Llama Mapping) to produce the mappings.

## Installation and Setup

1. Clone the repository:

```bash
git clone https://github.com/yourusername/graphindex.git
cd graphindex
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```
3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage
Make sure you have activated the virtual environment:

```bash
source venv/bin/activate   
# On Windows: venv\Scripts\activate
```

### Start the Flask app:
Before starting the Flask app define the following environment variables:
```bash
OPENAI_API_KEY='<your_api_key>'
SOURCE_DIR='<path_to_store_or_read_local_ontology>'
OUTPUT_DIR='<path_to_store_or_read_local_index>'
LOGS_DIR='<path_to_store_app_logs>'
OPENAI_MODEL='<openai_model_to_generate_mapping>'
VALIDATION_MODEL='<openai_model_for_two_step_validation>'
```
Run the Flask app
```bash
python app.py
```
Once the app is running, you can access the API endpoint to get the semantic mapping. Use a tool like curl or Postman to make a POST request to http://localhost:5000/api/v1/mapping with a CSV file representing the table you want to map
and providing the project id.

Optionally, you can provide your own ontology stored in a local folder. The app will use the default schema.org if no custom ontology is specified.

To do this, specify the path to the local ontology in the SemanticMapper object:

```python
from src.graphindex.mapping import SemanticMapper
from src.graphindex.common.enumerations import IndexType
    
mapper = SemanticMapper(
    ontology_source_dir='<path_to_local_ontology>',
    index_output_dir='<path_to_store_index>',
    openai_model='gpt-3.5-turbo-16k',
    index_type=IndexType.VECTOR
)
```

## Project Structure
src/graphindex: Contains the logic and implementation of the semantic mapping.

app.py: Flask app file with the API endpoint for mapping table columns to ontology terms.

examples: Contains example CSV files for testing the API.

requirements.txt: Lists the required dependencies for the project.
