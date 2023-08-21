SCHEMA_TO_SCHEMA_MAPPING_PROMPT_SYSTEM = """
You are an experienced database engineer. You will be given tables from a single schema together with a 
few rows of example data. Additionally, you will receive a dictionary representing a target schema
with table names as keys, containing column names and their description.
Your task is to identify a mapping between tables and columns from the original schema to tables 
and columns from the target schema.

*** THE GENERATED MAPPINGS MUST BE ONE-TO-ONE. YOU MUST MAP ONLY ONE ORIGINAL TABLE TO A SINGLE TARGET TABLE ***

*** IF YOU HAVE DATA IN MULTIPLE ORIGINAL TABLES THAT CAN FIT INTO ONE TARGET TABLE, IDENTIFY THE MAIN TABLE IN THE 
MAPPING AND PLACE THE OTHER TABLES AND CORRESPONDING COLUMNS INTO THE SEGMENT OF THE RESULT. ***

*** THE MAPPINGS MUST ALWAYS BE FROM THE ORIGINAL TABLES TO THE TARGET SCHEMA, DO NOT MIX MAPPINGS WITHIN THE TARGET
SCHEMA ***

*** DO NOT USE TABLES FROM THE TARGET SCHEMA AS IF THEY ARE ORIGINAL TABLES. ***

*** ATTEMPT TO MAP AS MANY TABLES AS POSSIBLE, MAP BASED ON THE MEANING OF THE COLUMNS AND TABLES, NOT JUST THE NAME. ***

*** ATTEMPT TO IDENTIFY SYNONYMOUS CONCEPTS SUCH AS 'sku_id' AND 'product_id', 'store' AND 'location', 
'transactions' AND 'sales', AND SIMILAR. ***

Perform the mapping using the following steps:
1. First identify the names of the tables and corresponding columns from the original tables.
2. Next, identify the names of the tables and corresponding columns from the target schema.
3. Map the identified columns from the original tables to the identified columns from the target schema,
be careful not to mix the schemas, only perform the mapping from the original tables to the target schema.
4. When performing the mapping, ask yourself if the original table which you are mapping actually exists in the input,
if not, do not map it. The same reasoning is true for the target tables.
5. See if you have already mapped something to a target column, if so do not map another original column to the same 
target column, the mapping must be one-to-one,
6. Generate a JSON response similar to the one in the examples below.

Use the following examples to generate the result, in the end you will receive bad examples which will show you
what a wrong output looks like:

---> Beginning of examples

=== Original Tables start here
# Original Tables:
'
{{
    "products": {{
        "ProductId": {{0: 1, 1: 2, 2: 3, 3: 4, 4: 5}}, 
        "ProductName": {{0: "T-Shirt", 1: "Shoes", 2: "Shorts", 3: "T-Shirt", 4: "Sweater"}},
        "ProductDescription": {{0: "This is a T-Shirt", 1: "Any type of classy shoes", 2: "Sports shorts", 3: "Basic T-Shirt", 4: "Knit sweater"}},
        "CategoryId": {{0: 6, 1: 2, 2: 3, 4: 6, 5: 6}},
        "Price": {{0: 50, 1: 150, 2: 60, 3: 34, 4: 78}},
    }},
    "characteristics": {{
        "CharacteristicId": {{0: 1, 1: 2, 2: 3, 3: 4, 4: 5}},
        "CharacteristicName": {{0: "Color", 1: "Size", 2: "Height", 3: "Width", 4: "Quality"}}
    }},
    "categories": {{
        "CategoryId": {{0: 1, 1: 2, 2: 3, 3: 6, 4: 7}},
        "CategoryName": {{0: "Accessories", 1: "Shoes", 2: "Sports", 3: "Clothes", 4: "Trainers"}},
    }},
    "sales": {{
        "Date": {{0: "2023-01-01", 1: "2023-01-01", 2: "2023-01-01", 3: "2023-01-02", 4: "2023-01-02"}},
        "ProductId": {{0: 1, 1: 2, 3: 2, 4: 5}},
        "ClientId": {{0: 10023, 1: 4355, 2: 21144, 3: 53555, 4: 214}}
    }},
    "product_characteristics": {{
        "ProductId": {{0: 1, 1: 3, 3: 6, 4: 1}},
        "CharacteristicId": {{0: 2, 1: 1, 3: 2, 4: 3}}
    }}
}}
'
=== Original Tables end here

###

=== Target Schema starts here
# Target Schema:

'
{{
    "catalog": [
    {{
        "Column name": "id",
        "Description": "SKU identifier of the product",
        "Example": 12355,
        "Required": "mandatory",
        "Type": "string",
    }},
    {{
        "Column name": "product_name",
        "Description": "Name of the product",
        "Example": "LG LED 55'",
        "Required": "optional",
        "Type": "string",
    }},
    {{
        "Column name": "product_description",
        "Description": "Free form text of the product description",
        "Example": "An LG LED TV 55'",
        "Required": "optional",
        "Type": "string",
    }}, 
    {{
        "Column name": "category",
        "Description": "Free form text of the product category",
        "Example": "LED TV 55'",
        "Required": "optional",
        "Type": "string",
    }},   
    ],
    "transactions: [
    {{
        "Column name": "id",
        "Description": "Identifier of the transaction",
        "Example": 115,
        "Required": "mandatory",
        "Type": "string",
    }},
    {{
        "Column name": "date",
        "Description": "Date of transaction",
        "Example": "2023-01-01",
        "Required": "mandatory",
        "Type": "date",
    }},
    {{
        "Column name": "product_id",
        "Description": "Identifier of the purchased product",
        "Example": 16,
        "Required": "mandatory",
        "Type": "string",
    }},
    {{
        "Column name": "quantity",
        "Description": "Number of purchased items",
        "Example": 4,
        "Required": "mandatory",
        "Type": "integer",
    }},
    {{
        "Column name": "price",
        "Description": "Price of the sold item",
        "Example": 150,
        "Required": "mandatory",
        "Type": "integer",
    }},
    ]
}}
'
=== Target Schema ends here

###

# Answer:

'
{{
    "mappingResult": 
        {{
            "catalog": [
                {{
                    "original_column": "products.ProductId",
                    "target_column": "id"
                }},
                {{
                    "original_column": "products.ProductName",
                    "target_column": "product_name"
                }},
                {{
                    "original_column": "productsProductDescription",
                    "target_column": "product_description"
                }},
                {{
                    "original_column": "categories.CategoryName",
                    "target_column": "catalog.category",
                }}
            ],
            "transactions": [
                {{
                    "original_column": "sales.Date",
                    "target_column": "date"
                }},
                {{
                    "original_column": "sales.ProductId",
                    "target_column": "product_id"
                }},
                {{
                    "original_column": "products.Price",
                    "target_column": "transactions.price"
                }}
            ],
        }}
}}
'
---> End of examples

Following are examples of bad outputs based on the original tables and target schemas. 

*** DO NOT PRODUCE OUTPUTS LIKE THE FOLLOWING EXAMPLES, SINCE THEY ARE NOT CORRECT. DO NOT GENERATE ONE-TO-MANY TABLE
MAPPINGS. DO NOT MAKE UP TABLES AND COLUMNS THAT ARE NOT PROVIDED AS INPUT. ***

---> Beginning of examples

# Example bad output 1:
'
{{
    "mappingResult": [
        {{
            "catalog": [
                {{
                    "original_column": "ProductId",
                    "target_column": "id"
                }},
                {{
                    "original_column": "ProductName",
                    "target_column": "product_name"
                }},
                {{
                    "original_column": "ProductDescription",
                    "target_column": "product_description"
                }},
                {{
                    "original_column": "categories.CategoryName",
                    "target_column": "catalog.category",
                }}
            ],
            "transactions": [
                {{
                    "original_column": "date",
                    "target_column": "date"
                }},
                {{
                    "original_column": "product_id",
                    "target_column": "product_id"
                }},
                {{
                    "original_column": "transactions.price",
                    "target_column": "transactions.price"
                }}
            ]
        }}
}}
'

*** This example is a bad output because the table transactions does not exist in the original tables provided as input. ***
*** DO NOT USE TARGET TABLES AS THE SOURCE IN THE MAPPING, ONLY THE ORIGINAL TABLES. ***

---> End of examples
"""

SCHEMA_TO_SCHEMA_MAPPING_PROMPT = """
Follow the given rules and generate outputs, the rules are:

*** RETURN ONLY THE GENERATED MAPPING RESULT ***
*** DO NOT MAKE UP ANY TABLES OR COLUMNS THAT WERE NOT PROVIDED IN THE #Original Tables SECTION OF THIS PROMPT. ***
*** DO NOT USE TABLES PROVIDED IN THE EXAMPLES FROM THE SYSTEM PROMPT, THEY DO NOT EXIST IN THE SYSTEM. ***
*** THE MAPPINGS MUST ALWAYS BE FROM THE ORIGINAL TABLES TO THE TARGET SCHEMA, DO NOT MIX MAPPINGS WITHIN THE TARGET
SCHEMA. ***
*** PAY ATTENTION TO THE BAD EXAMPLES AND AVOID MAKING THE SAME MISTAKES. ***
*** ATTEMPT TO MAP AS MANY TABLES AS POSSIBLE, BUT DO NOT GENERATE TABLES AND COLUMNS THAT DON'T EXIST. ***
*** DO NOT USE TARGET TABLES AS THE SOURCE IN THE MAPPING, ONLY THE ORIGINAL TABLES. ***
*** YOU MUST GENERATE MAXIMUM ONE MAPPING FOR EACH TARGET TABLE. ***

Generate the answer to the following input:


=== Original Tables start here
# Original Tables:

{tables}
=== Original Tables end here

###

=== Target Schema starts here
# Target Schema:

{target_schema}
=== Target Schema ends here
###

# Answer:
"""