import json
import logging
import os
import time
import dotenv
from flask import Flask, request, jsonify
import pandas as pd

from src.graphindex.chat import GraphIndexBot
from src.graphindex.common.enumerations import IndexType
from src.graphindex.mapping import SemanticMapper
dotenv.load_dotenv()

src_dir = os.getenv('SOURCE_DIR')
out_dir = os.getenv('OUTPUT_DIR')
logs_dir = os.getenv('LOGS_DIR')

OPENAI_MODEL = os.getenv('OPENAI_MODEL')
VALIDATION_MODEL = os.getenv('VALIDATION_MODEL')

logfile = f'{logs_dir}/{time.time()}.txt'

logging.basicConfig(filename=logfile, level=logging.INFO)
logging.getLogger().addHandler(logging.FileHandler(filename=logfile))

bot = GraphIndexBot()

app = Flask(__name__)

@app.route('/api/v1/mapping', methods=['POST'])
def map_column_names_to_ontology_terms():
    # Check if the request contains a file
    file = check_file_is_valid('file')
    project_id = request.form.get('project_id')
    check_project_id_is_valid(project_id)
    description = request.form.get('description')

    logging.info(f"Started mapping for project with id: {project_id}")

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
            description=description,
            check_answers_llm=VALIDATION_MODEL
        )
        result["project_id"] = project_id

        return jsonify({"status": "success", "message": result})
    except Exception as err:
        return jsonify({"status": "error", "message": f"Internal server error: {err}"}), 500


@app.route('/api/v1/chat', methods=['POST'])
def chat():
    file = check_file_is_valid('file')
    project_id = request.form.get("project_id")
    check_project_id_is_valid(project_id)
    question = request.form.get("messageText")
    mapping = request.form.get("mapping")
    description = request.form.get("description")

    if not question:
        return jsonify({"status": "error", "message": f"Invalid message sent by the user."}), 400

    if not mapping:
        return jsonify({"status": "error", "message": f"Empty mapping sent."}), 400

    df = try_read_csv(file)
    data_sample = json.dumps(df.head(10).to_dict())

    try:
        answer = bot.chat(
            project_id,
            question,
            data_sample,
            mapping,
            description
        )
        return jsonify({"status": "success", "message": answer})
    except Exception as err:
        return jsonify({"status": "error", "message": f"Internal server error: {err}"}), 500


def try_read_csv(file):
    # Read the CSV file
    try:
        return pd.read_csv(file)
    except Exception as err:
        return jsonify({"status": "error", "message": f"Error reading the CSV file. {err}"}), 500


def check_project_id_is_valid(project_id):
    if not project_id:
        return jsonify({"status": "error", "message": "Invalid project id"}), 404


def check_file_is_valid(file_key):
    if file_key not in request.files:
        return jsonify({"status": "error", "message": "No file part"}), 400

    file = request.files[file_key]

    if file.filename == '' or not file.filename.lower().endswith('.csv'):
        return jsonify({"status": "error", "message": "Invalid file format. Only CSV files are allowed."}), 400
    return file


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
