import json
import logging
import os
import time

from flask import Flask, request, jsonify
import pandas as pd
from werkzeug.utils import secure_filename

from src.graphindex.chat import GraphIndexBot
from src.graphindex.common.enumerations import IndexType
from src.graphindex.index import ColumnIndex
from src.graphindex.mapping import SemanticMapper, TablesMapper

src_dir = os.environ.get('SOURCE_DIR')
out_dir = os.environ.get('OUTPUT_DIR')
logs_dir = os.environ.get('LOGS_DIR')

OPENAI_MODEL = os.environ.get('OPENAI_MODEL')
VALIDATION_MODEL = os.environ.get('VALIDATION_MODEL')

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
            tables=data_summary,
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
        return jsonify({"status": "error", "message": f"Error initiating chat: {err}"}), 500


@app.route('/api/v1/keys-mapping', methods=['POST'])
def map_keys():
    project_id = request.form.get("project_id")
    check_project_id_is_valid(project_id)
    files = request.files.getlist('file')
    dataframes_dict = read_tables_for_mapping(files)

    try:
        index = ColumnIndex(
            dataframes_dict,
            output_dir=f"{out_dir}/column/{project_id}",
            openai_model=OPENAI_MODEL
        )
        return jsonify({"status": "success", "message": index.get_index()})
    except Exception as err:
        return jsonify({"status": "error", "message": f"Error creating index: {err}"}), 500


@app.route('/api/v1/generate_queries', methods=['POST'])
def generate_queries():

    project_id = request.form.get("project_id")
    check_project_id_is_valid(project_id)
    files = request.files.getlist('file')
    dataframes_dict = read_tables_for_mapping(files)
    schemas = request.files.getlist('target_schemas')
    schemas_dict = read_tables_for_mapping(schemas, are_schemas=True)

    try:
        mapper = TablesMapper(
            dataframes_dict,
            project_id=project_id,
            index_output_dir=f"{out_dir}/column"
        )

        mapping, sql = mapper.map(target_schemas=schemas_dict)

        mapping = json.loads(mapping)

        mapping["queries"] = sql

        return jsonify({"status": "success", "message": mapping})
    except Exception as err:
        return jsonify({"status": "error", "message": f"Error generating queries: {err}"}), 500


def read_tables_for_mapping(uploaded_files, are_schemas=False):
    if not len(uploaded_files):
        return jsonify({"status": "error", "message": f"No files were provided for mapping."}), 404

    dataframes_dict = {}

    for file in uploaded_files:
        if file and check_file_is_valid(file.filename):
            filename = read_file_name(file)
            df = try_read_csv(file)
            if are_schemas:
                df = df.to_dict(orient="records")

            dataframes_dict[filename] = df

    return dataframes_dict


def read_file_name(file):
    filename = secure_filename(file.filename)
    filename = filename.replace(".csv", "")
    return filename


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
        return jsonify({
            "status": "error",
            "message": f"Invalid file format for {file.filename}. Only CSV files are allowed."
        }), 400
    return file


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
