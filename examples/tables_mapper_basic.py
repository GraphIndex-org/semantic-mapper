import pandas as pd

from src.graphindex.mapping import TablesMapper

if __name__ == '__main__':
    data_path = "./data/spider"
    tables = {
        "characteristics": pd.read_csv(f'{data_path}/Characteristics.csv'),
        "products_characteristics": pd.read_csv(f'{data_path}/Product_Characteristics.csv'),
        "products": pd.read_csv(f'{data_path}/Products.csv'),
        "ref_characteristic_types": pd.read_csv(f'{data_path}/Ref_Characteristic_Types.csv'),
        "ref_colors": pd.read_csv(f'{data_path}/Ref_Colors.csv'),
        "ref_product_categories": pd.read_csv(f'{data_path}/Ref_Product_Categories.csv'),
        "store": pd.read_csv(f"{data_path}/store.csv"),
        "district": pd.read_csv(f"{data_path}/district.csv"),
        "store_district": pd.read_csv(f"{data_path}/store_district.csv"),
        "store_product": pd.read_csv(f"{data_path}/store_product.csv"),
        "sales_header": pd.read_csv(f"{data_path}/sales_header.csv"),
        "sales_details": pd.read_csv(f"{data_path}/sales_details.csv"),
    }

    schemas = {
        "catalog": pd.read_csv('./data/schemas/catalog.csv').to_dict(orient="records"),
        "locations": pd.read_csv('./data/schemas/locations.csv').to_dict(orient="records"),
        "transactions": pd.read_csv('./data/schemas/transactions.csv').to_dict(orient="records"),
        "inventory_status": pd.read_csv('./data/schemas/inventory_status.csv').to_dict(orient="records")
    }

    mapper = TablesMapper(
        tables,
        project_id="185",
        index_output_dir="../indices/column"
    )

    transformations = mapper.map(target_schemas=schemas)
    print(transformations)
