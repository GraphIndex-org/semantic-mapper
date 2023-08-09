import json

import pandas as pd

from src.graphindex.common.enumerations import IndexType
from src.graphindex.mapping import SemanticMapper
import logging
import time

# Log steps to file
logfile = f'../logs/{time.time()}.txt'

logging.basicConfig(filename=logfile, level=logging.DEBUG)
logging.getLogger().addHandler(logging.FileHandler(filename=logfile))

if __name__ == '__main__':

    data = pd.read_csv('C:/Users/mimi_/Desktop/Purchases.csv')

    mapper = SemanticMapper(
        ontology_source_dir='../schemas',
        index_output_dir='../indices',
        openai_model='gpt-3.5-turbo-16k',
        index_type=IndexType.VECTOR
    )
    res = mapper.map(
        columns=data.head(10).to_dict(),
        description="The table contains data about product purchases. It includes customer identifiers, shipping information, dates of shipment, documents related to the shipments and price information.",
        check_answers_llm='gpt-4'
    )

    with open('data/mapping_result_fashion.json', 'w') as f:
        f.write(json.dumps(res))
