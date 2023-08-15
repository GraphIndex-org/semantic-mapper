import json
from typing import Dict

import openai
import pandas as pd
import requests
import os

from llama_index.llms import OpenAI
from llama_index.graph_stores import SimpleGraphStore

from src.graphindex.common.config import (
    SCHEMA_ORG_URI,
    SCHEMA_ORG_LOCAL_PATH_SUBGRAPHS,
    SCHEMA_ORG_LOCAL_PATH,
    SCHEMA_ORG_INDEX_LOCAL_PATH,
    SCHEMA_FILE_NAME
)

from llama_index import (
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage,
    SimpleDirectoryReader,
    KnowledgeGraphIndex,
    ServiceContext, OpenAIEmbedding
)

from src.graphindex.common.prompts import TABLES_MAPPING_PROMPT, TABLES_MAPPING_PROMPT_SYSTEM
from src.graphindex.common.utils import (
    create_graph_from_jsonld,
    save_subjects_to_files,
    extract_subgraph_for_each_subject
)

from src.graphindex.common.enumerations import IndexType


class OntologyIndex:
    def __init__(
            self,
            index_type: IndexType,
            source_dir='./schemas',
            output_dir='./index',
            use_schema_org: bool = False,
            ontology_version: str = None
    ) -> None:
        self.uri = SCHEMA_ORG_URI.format(ontology_version=ontology_version)
        self.index_type = index_type
        self.schema_file_name = SCHEMA_FILE_NAME

        if use_schema_org:
            self.schema_local_path = SCHEMA_ORG_LOCAL_PATH.format(
                src_dir=source_dir,
                ontology_version=ontology_version
            )
            self.local_index = SCHEMA_ORG_INDEX_LOCAL_PATH.format(
                output_dir=output_dir,
                ontology_version=ontology_version,
                index_type=str.lower(self.index_type.name)
            )
            self.subgraphs_path = SCHEMA_ORG_LOCAL_PATH_SUBGRAPHS.format(
                src_dir=source_dir,
                ontology_version=ontology_version
            )

        else:
            self.schema_local_path = source_dir
            self.local_index = output_dir
            self.subgraphs_path = f"{source_dir}/subgraphs"

        self.index = None
        self.ontology_version = ontology_version
        self.use_schema_org= use_schema_org

    def _is_local_ontology(self):
        local_path = self.schema_local_path

        if os.path.isdir(local_path):
            return True

        os.makedirs(local_path)
        return False

    def _load_local_index(self):
        local_index = self.local_index

        if os.path.isdir(local_index):
            storage_context = StorageContext.from_defaults(persist_dir=local_index)
            return load_index_from_storage(storage_context)

        os.makedirs(local_index)

        return None

    def _load_schema_org_ontology(self):
        if not self._is_local_ontology():
            release_uri = self.uri

            response = requests.get(release_uri)

            if response.status_code != 200:
                raise Exception(f"Failed to fetch schema.org version {self.ontology_version}. \
                            Status code: {response.status_code}")

            result = response.json()

            graph = create_graph_from_jsonld(result)
            subjects_with_props = extract_subgraph_for_each_subject(graph)
            save_subjects_to_files(
                subjects_with_props,
                self.subgraphs_path
            )

    def _transform_graph_to_vector_store(self):
        try:
            index = self._load_local_index()
        except Exception as err:
            raise Exception("Could not read local index.")

        if not index:
            schema_path = self.subgraphs_path
            index_path = self.local_index

            documents = SimpleDirectoryReader(schema_path).load_data()

            if self.index_type == IndexType.VECTOR:
                index = VectorStoreIndex.from_documents(documents)

            elif self.index_type == IndexType.KNOWLEDGE_GRAPH:
                graph_store = SimpleGraphStore()
                storage_context = StorageContext.from_defaults(graph_store=graph_store)

                llm = OpenAI(temperature=0, model="gpt-3.5-turbo")
                service_context = ServiceContext.from_defaults(llm=llm, chunk_size=512)

                # NOTE: can take a while!
                index = KnowledgeGraphIndex.from_documents(
                    documents,
                    max_triplets_per_chunk=3,
                    storage_context=storage_context,
                    service_context=service_context,
                )
            else:
                raise NotImplementedError()

            index.storage_context.persist(persist_dir=index_path)

        self.index = index

    def create_index_from_ontology_version(self):
        if self.use_schema_org:
            self._load_schema_org_ontology()
        self._transform_graph_to_vector_store()

    def get_index(self):
        return self.index


def jaccard(list1, list2):
    intersection = len(list(set(list1).intersection(list2)))
    union = len(list((set(list1).union(set(list2)))))
    return intersection / union if union else 0


class ColumnIndex:
    def __init__(self, tables: Dict[str, pd.DataFrame], index_path: str = "./index"):
        self.tables = tables
        self.index_path = index_path
        self.embed_model = OpenAIEmbedding()
        self.index = self._create_column_index(self.tables)

    def _create_column_index(self, tables: Dict[str, pd.DataFrame]):
        index = {}
        similarity = {}

        for table_name, table in tables.items():
            for col_name, col_data in table.items():
                data_list = sorted(col_data.dropna().astype(str).unique())

                if not len(data_list):
                    continue

                embedding = data_list[:100]
                similarity[f"{table_name}.{col_name}"] = embedding

        for table_col, embedding in similarity.items():
            for table_col2, embedding2 in similarity.items():
                if table_col == table_col2 or (table_col.split(".")[0] == table_col2.split(".")[0]):
                    continue
                sim = jaccard(embedding, embedding2)
                if sim > 0.6:
                    if table_col not in index:
                        index[table_col] = [(table_col2, sim)]
                    else:
                        index[table_col].append((table_col2, sim))

        self._save_index(index, similarity)
        return index

    def _save_index(self, index, embeddings):
        with open(f"{self.index_path}/index.json", "w") as f:
            f.write(json.dumps(index))
        with open(f"{self.index_path}/embeddings.json", "w") as f:
            f.write(json.dumps(embeddings))

    def retrieve_connected_tables(self, query, filter_similarity=0.7):
        table_columns = [tc for tc in self.index.keys() if query == tc.split(".")[0]]
        joins = []
        for tc in table_columns:
            for val in self.index[tc]:
                if val[1] > filter_similarity:
                    joins.append((tc, val[0]))

        return joins


if __name__ == '__main__':
    tables = {
        "characteristics": pd.read_csv('../../examples/data/spider/Characteristics.csv'),
        "products_characteristics": pd.read_csv('../../examples/data/spider/Product_Characteristics.csv'),
        "products": pd.read_csv('../../examples/data/spider/Products.csv'),
        "ref_characteristic_types": pd.read_csv('../../examples/data/spider/Ref_Characteristic_Types.csv'),
        "ref_colors": pd.read_csv('../../examples/data/spider/Ref_Colors.csv'),
        "ref_product_categories": pd.read_csv('../../examples/data/spider/Ref_Product_Categories.csv'),
    }

    schemas = {
        "catalog": pd.read_csv('../../examples/data/schemas/catalog.csv').to_dict(orient="records")
    }

    idx = ColumnIndex(tables, index_path="../../indices/column/custom")

    joins = idx.retrieve_connected_tables("products", filter_similarity=0.7)
    linked_tables = [j[1].split(".")[0] for j in joins]
    linked_tables.append("products")
    table_data = {k: v.head(10).to_dict() for k, v in tables.items() if k in linked_tables}

    system_prompt = TABLES_MAPPING_PROMPT_SYSTEM

    prompt = TABLES_MAPPING_PROMPT.format(
        tables=json.dumps(table_data),
        joins=json.dumps(joins),
        target_schema=json.dumps(schemas)
    )

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    )

    print(response)
