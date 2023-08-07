import logging
import os
import time

from flask import Flask, request, jsonify
import pandas as pd

from src.graphindex.common.enumerations import IndexType
from src.graphindex.mapping import SemanticMapper


src_dir = os.environ.get('SOURCE_DIR')
out_dir = os.environ.get('OUTPUT_DIR')
logs_dir = os.environ.get('LOGS_DIR')

OPENAI_MODEL = os.environ.get('OPENAI_MODEL')
VALIDATION_MODEL = os.environ.get('VALIDATION_MODEL')

logfile = f'{logs_dir}/{time.time()}.txt'

logging.basicConfig(filename=logfile, level=logging.INFO)
logging.getLogger().addHandler(logging.FileHandler(filename=logfile))


app = Flask(__name__)


@app.route('/api/v1/mapping', methods=['POST'])
def map_column_names_to_ontology_terms():
    # Check if the request contains a file
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part"}), 400

    project_id = request.form.get('project_id')
    logging.info(f"Started mapping for project with id: {project_id}")

    if not project_id:
        return jsonify({"status": "error", "message": "Invalid project id"}), 404

    file = request.files['file']

    # Check if the file is a CSV file
    if file.filename == '' or not file.filename.lower().endswith('.csv'):
        return jsonify({"status": "error", "message": "Invalid file format. Only CSV files are allowed."}), 400

    # Read the CSV file
    try:
        df = pd.read_csv(file)
    except Exception as err:
        return jsonify({"status": "error", "message": f"Error reading the CSV file. {err}"}), 500

    data_summary = df.head(10).to_dict()

    try:
        mapper = SemanticMapper(
            ontology_source_dir=src_dir,
            index_output_dir=out_dir,
            openai_model=OPENAI_MODEL,
            index_type=IndexType.VECTOR
        )
        result = mapper.map(
            columns=data_summary,
            check_answers_llm=VALIDATION_MODEL
        )
        result["project_id"] = project_id

        return jsonify({"status": "success", "message": result})
    except Exception as err:
        return jsonify({"status": "error", "message": f"Internal server error: {err}"}), 500


if __name__ == '__main__':
    app.run(debug=True)
