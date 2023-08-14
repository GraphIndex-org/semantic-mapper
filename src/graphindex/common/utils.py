import json
import os
from typing import Dict

import numpy as np
import pandas as pd
from rdflib import Graph, RDFS, Namespace, Literal


def create_graph_from_jsonld(jsonld_data: json):
    graph = Graph()
    graph.parse(data=json.dumps(jsonld_data), format='json-ld')
    return graph


def extract_subjects_with_properties_from_graph(graph: Graph):
    subjects_with_predicates = {}
    for subject, predicate, obj in graph:
        subject_str = str(subject)
        predicate_str = str(predicate)
        obj_str = str(obj)

        subject_comment, predicate_comment, object_comment = None, None, None

        if subject_str not in subjects_with_predicates:
            subjects_with_predicates[subject_str] = []

        for _, _, comment in graph.triples((subject, RDFS.comment, None)):
            subject_comment = str(comment)

        for _, _, comment in graph.triples((obj, RDFS.comment, None)):
            object_comment = str(comment)

        for _, _, comment in graph.triples((predicate, RDFS.comment, None)):
            predicate_comment = str(comment)

        subjects_with_predicates[subject_str].append({
            "predicate": predicate_str,
            "predicate_comment": predicate_comment,
            "object": obj_str,
            "object_comment": object_comment,
        })

    for subject, predicate, obj in graph:
        subject_str = str(subject)
        predicate_str = str(predicate)
        obj_str = str(obj)
        subject_comment, predicate_comment = None, None

        for _, _, comment in graph.triples((subject, RDFS.comment, None)):
            subject_comment = str(comment)

        for _, _, comment in graph.triples((predicate, RDFS.comment, None)):
            predicate_comment = str(comment)

        if obj_str in subjects_with_predicates:
            subjects_with_predicates[obj_str].append({
                "predicate": predicate_str,
                "predicate_comment": predicate_comment,
                "subject": subject_str,
                "subject_comment": subject_comment
            })

    return subjects_with_predicates


def save_subjects_to_files(subjects_with_predicates: Dict[str, Dict[str, str]], local_path: str):
    if not os.path.isdir(local_path):
        os.makedirs(local_path)

    for subject, predicates in subjects_with_predicates.items():
        subject_name = subject.split("/")[-1]
        filename = f"{local_path}/{subject_name}.json"
        with open(filename, 'w') as f:
            f.write(json.dumps(predicates, indent=2))


def extract_subgraph_for_each_subject(graph: Graph):
    subgraphs_with_comments = {}
    ns_rdfs = Namespace("http://www.w3.org/2000/01/rdf-schema#")

    for subject in graph.subjects():
        subgraph = Graph()
        subgraph.bind("rdfs", ns_rdfs)

        # Add triples for the subject
        for s, p, o in graph.triples((subject, None, None)):
            subgraph.add((s, p, o))

        # Add triples for objects connected to the subject
        for s, p, o in graph.triples((None, None, subject)):
            subgraph.add((s, p, o))

        # Add rdfs:comment for subject if available
        subject_comment = None
        for _, _, comment in graph.triples((subject, RDFS.comment, None)):
            subject_comment = str(comment)
        if subject_comment:
            subgraph.add((subject, RDFS.comment, Literal(subject_comment)))

        # Add rdfs:comment for predicates and objects
        for s, p, o in subgraph:
            obj_comment = None
            for _, _, comment in graph.triples((o, RDFS.comment, None)):
                obj_comment = str(comment)
            if obj_comment:
                subgraph.add((o, RDFS.comment, Literal(obj_comment)))

        subgraphs_with_comments[subject] = subgraph.serialize(format='json-ld')

    return subgraphs_with_comments


def check_is_column_identifier(col, min_unique_values=0.99):
    if col.nunique() / len(col) >= min_unique_values:
        return True
    return False


def calculate_data_summary(dataset: pd.DataFrame):
    """
    Calculates a summary for all columns in a dataframe, including unique values, most frequent values,
    number of missing values, statistics for numeric features
    :param dataset: pd.DataFrame - a pandas dataframe
    :return: dict - A dictionary with column names as keys and calculated statistics as values
    """
    result = {}
    for col_name, col_data in dataset.items():
        num_null_values = col_data.isnull().sum()
        if check_is_column_identifier(col_data):
            result[col_name] = {
                "is_identifier": True,
                "num_unique_values": str(col_data.nunique()),
                "num_null_values": str(num_null_values),
                "count": str(col_data.count())
            }
        elif col_data.dtype == object:  # Check if the column contains string data
            top_values = col_data.value_counts().head(5).to_dict()
            num_unique_values = col_data.nunique()
            result[col_name] = {
                "top_values": str(top_values),
                "num_unique_values": str(num_unique_values),
                "num_null_values": str(num_null_values),
                "count": str(col_data.count()),
            }
        else:
            result[col_name] = {
                "count": str(col_data.count()),
                "mean": str(col_data.mean()),
                "std": str(col_data.std()),
                "min": str(col_data.min()),
                "25%": str(col_data.quantile(0.25)),
                "50%": str(col_data.quantile(0.50)),
                "75%": str(col_data.quantile(0.75)),
                "max": str(col_data.max()),
                "num_null_values": str(num_null_values),
            }
    return result
