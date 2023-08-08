import json

import pandas as pd

from src.graphindex.chat import GraphIndexBot

if __name__ == '__main__':
    data = pd.read_csv('./data/fashion_products.csv')
    with open('data/mapping_result_fashion.json', 'r') as f:
        mapping = f.read()

    data_sample = json.dumps(data.head(10).to_dict())

    bot = GraphIndexBot()
    answer = bot.chat(123, "Why is the column Product ID mapped to sku?", data_sample, mapping)
    print(answer)
    answer = bot.chat(123, "What kind of values does the column Size contain?", data_sample, mapping)
    print(answer)
    answer = bot.chat(46, "What kind of values does the column Brand contain?", data_sample, mapping)
    print(answer)

