TABLES_MAPPING_PROMPT_SYSTEM = """
You are an experienced database engineer. You are going to receive a sample of multiple database tables together
with information on how to join the tables together. Your task is to map this set of tables into a provided target 
schema. The information of the schema describes the columns and the possible values in each column. 

*** The name of the schema of the provided tables is 'dbo', and the name of the target schema is 'target'. ***

Follow the given rules separated with the symbols '***'.

*** THE INFORMATION ABOUT THE JOINS MIGHT BE INCORRECT. YOUR TASK IS TO BE ABLE TO IDENTIFY
WHICH OF THE SUGGESTED JOIN RULES ARE CORRECT AND WHICH ARE NOT. DO NOT OUTPUT THIS INFORMATION. IF THE IDENTIFIERS
ARE MARKED AS JOINS BUT THEY HAVE DIFFERENT NAMES, THEN THIS IS PROBABLY NOT A CORRECT JOIN. ***

*** IGNORE JOIN RULES THAT ARE INCORRECT. ***
*** JOIN ONLY NECESSARY TABLES, DO NOT USE ALL JOINS IF THEY ARE NOT NEEDED. ***
*** USE SINGLE QUOTES WHEN REFERRING TO COLUMN NAMES ***
*** DO NOT MAKE UP TABLES THAT DON'T EXIST. ***
*** ATTEMPT TO MAP AS MUCH TABLES AS YOU CAN, BUT THE MAPPING MUST BE MEANINGFUL. ***
*** INSERT INTO EACH TARGET TABLE MAXIMUM ONCE. ****

Execute the task using the following steps:

1. Map the columns from the provided tables to the columns of the target schema based on their meaning. For each
column you will be provided with a few example values.

*** You must map to all columns defined as mandatory. ***

2. After you have mapped the input columns to the target schema columns, write a SQL query which will complete the
mapping. Do not write any DDL, only output SQL queries for extracting and transforming data to the target schema.

*** USE THE COLUMN NAMES DEFINED IN THE TARGET SCHEMA. DO NOT GENERATE NEW COLUMNS IN THE TARGET SCHEMA. ***
*** USE THE COLUMNS DEFINED IN THE KEY 'column_name' FROM THE TARGET SCHEMA. ***
*** CREATE INSERT STATEMENTS ON THE TARGET SCHEMA AND SELECT FROM THE PROVIDED TABLES. ***

Use the following examples to gain a better understanding of your task:

--> Beginning of examples:

# Tables:

'
{{
    "products": {{
        "ProductId": {{0: 1, 1: 2, 2: 3, 3: 4, 4: 5}}, 
        "ProductName": {{0: "T-Shirt", 1: "Shoes", 2: "Shorts", 3: "T-Shirt", 4: "Sweater"}},
        "ProductDescription": {{0: "This is a T-Shirt", 1: "Any type of classy shoes", 2: "Sports shorts", 3: "Basic T-Shirt", 4: "Knit sweater"}},
        "CategoryId": {{0: 6, 1: 2, 2: 3, 4: 6, 5: 6}},
        "Price": {{0: 50, 1: 150, 2: 60, 3: 34, 4: 78}},
    }},
    "categories": {{
        "CategoryId": {{0: 1, 1: 2, 2: 3, 3: 6, 4: 7}},
        "CategoryName": {{0: "Accessories", 1: "Shoes", 2: "Sports", 3: "Clothes", 4: "Trainers"}},
    }},
    "sales": {{
        "Date": {{0: "2023-01-01", 1: "2023-01-01", 2: "2023-01-01", 3: "2023-01-02", 4: "2023-01-02"}},
        "ProductId": {{0: 1, 1: 2, 3: 2, 4: 5}},
        "ClientId": {{0: 10023, 1: 4355, 2: 21144, 3: 53555, 4: 214}}
    }}
}}
'

###

# Joins:
'
{{
    "primaryKeys": [
        "products.ProductId",
        "categories.CategoryId",
        "sales.id",
        ["product_characteristics.product_id", "product_characteristics.characteristic_id"],
    ],
    "foreignKeys": [
        "products.CategoryId",
        "sales.ProductId",
        "sales.ClientId",
        "product_characteristics.product_id",
        "product_characteristics.characteristic_id",
    ]
    "joins": [
        ["products.ProductId", "sales.ProductId"],
        ["categories.CategoryId", "products.CategoryId"],
        ["products.ProductId", "product_characteristics.product_id"]
    ]
}}
'

### 

# Target Schema:

'
{{
    "catalog": [
    {{
        "column_name": "id",
        "description": "SKU identifier of the product",
        "example": 12355,
        "required": "mandatory",
        "type": "string",
    }},
    {{
        "column_name": "product_name",
        "description": "Name of the product",
        "example": "LG LED 55'",
        "required": "optional",
        "type": "string",
    }},
    {{
        "column_name": "product_description",
        "description": "Free form text of the product description",
        "example": "An LG LED TV 55'",
        "required": "optional",
        "type": "string",
    }},  
    ]
}}
'

###

# Schema Mapping:
'
{{
    "mappingResult": [
        {{
            "original_table": "products",
            "target_table": "catalog",
            "columns": [
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
                }}
            ]
        }},
        {{
            "original_table": "sales",
            "target_table": "transactions",
            "columns": [
                {{
                    "original_column": "Date",
                    "target_column": "date"
                }},
                {{
                    "original_column": "ProductId",
                    "target_column": "product_id"
                }},
            ],
            "columns_other_tables": [
                {{
                    "original_column": "products.Price",
                    "target_column": "transactions.price"
                }}
            ]
        }},
    ]
}}
'

###

# Answer:

'
INSERT INTO target.catalog ('id', 'product_name', 'product_description')
SELECT p.ProductId, p.ProductName, p.ProductDescription
FROM dbo.products as p; 
'

---> End of examples
"""

TABLES_MAPPING_PROMPT = """

*** RETURN ONLY THE GENERATED SQL QUERIES AND NOTHING ELSE ***

Using the previous example, generate the answer to the following input:

# Tables:

{tables}

###

# Joins:

{joins}

###

# Target Schema:

{target_schema}

###

# Schema Mapping:
{schema_mapping}

###

# Answer:
"""

TABLE_MAPPING_FEEDBACK_PROMPT_SYSTEM = """
You are an experienced database engineer. You will be given tables from a single schema together with a 
few rows of example data. Additionally, you will receive a target schema with table names, column names and their
description. You will be provided queries generated from gpt-3.5-turbo to map the original tables to the target schema.
Your task is to identify any wrong columns or tables in the SQL queries and fix them.

Follow the given rules separated with the symbols '***'.

*** The name of the schema of the provided tables is 'dbo', and the name of the target schema is 'target'. ***

*** THE INFORMATION ABOUT THE JOINS MIGHT BE INCORRECT. YOUR TASK IS TO BE ABLE TO IDENTIFY
WHICH OF THE SUGGESTED JOIN RULES ARE CORRECT AND WHICH ARE NOT. DO NOT OUTPUT THIS INFORMATION. ***

*** INSERT INTO THE EACH TARGET TABLE MAXIMUM ONCE. ***
*** REMOVE DUPLICATE AND ALMOST DUPLICATE STATEMENTS. ***
*** CORRECT JOIN RULES THAT ARE INCORRECT, FOLLOW THE JOIN RULES PROVIDED IN THE #Joins SEGMENT. ***
*** JOIN ONLY NECESSARY TABLES, DO NOT USE ALL JOINS IF THEY ARE NOT NEEDED. ***
*** USE SINGLE QUOTES WHEN REFERRING TO COLUMN NAMES ***
*** REMOVE TABLES FROM THE SQL QUERY THAT ARE NOT PROVIDED IN THE #Tables SEGMENT. ***
*** ATTEMPT TO MAP AS MUCH TABLES AS YOU CAN, BUT THE MAPPING MUST BE MEANINGFUL, DO NOT DUPLICATE DATA INSERTS. ***
*** USE THE COLUMN NAMES DEFINED IN THE TARGET SCHEMA. DO NOT GENERATE NEW COLUMNS IN THE TARGET SCHEMA. ***
*** USE THE COLUMNS DEFINED IN THE KEY 'column_name' FROM THE TARGET SCHEMA. ***
*** CREATE INSERT STATEMENTS ON THE TARGET SCHEMA AND SELECT FROM THE PROVIDED TABLES. ***

Use the following examples to gain a better understanding of your task:

--> Beginning of examples:

# Tables:
'
{{
    "products": {{
        "ProductId": {{0: 1, 1: 2, 2: 3, 3: 4, 4: 5}}, 
        "ProductName": {{0: "T-Shirt", 1: "Shoes", 2: "Shorts", 3: "T-Shirt", 4: "Sweater"}},
        "ProductDescription": {{0: "This is a T-Shirt", 1: "Any type of classy shoes", 2: "Sports shorts", 3: "Basic T-Shirt", 4: "Knit sweater"}},
        "CategoryId": {{0: 6, 1: 2, 2: 3, 4: 6, 5: 6}},
        "Price": {{0: 50, 1: 150, 2: 60, 3: 34, 4: 78}},
    }},
    "categories": {{
        "CategoryId": {{0: 1, 1: 2, 2: 3, 3: 6, 4: 7}},
        "CategoryName": {{0: "Accessories", 1: "Shoes", 2: "Sports", 3: "Clothes", 4: "Trainers"}},
    }},
    "sales": {{
        "Date": {{0: "2023-01-01", 1: "2023-01-01", 2: "2023-01-01", 3: "2023-01-02", 4: "2023-01-02"}},
        "ProductId": {{0: 1, 1: 2, 3: 2, 4: 5}},
        "ClientId": {{0: 10023, 1: 4355, 2: 21144, 3: 53555, 4: 214}}
    }}
}}
'

###

# Joins:
'
{{
    "primaryKeys": [
        "products.ProductId",
        "categories.CategoryId",
        "sales.id",
        ["product_characteristics.product_id", "product_characteristics.characteristic_id"],
    ],
    "foreignKeys": [
        "products.CategoryId",
        "sales.ProductId",
        "sales.ClientId",
        "product_characteristics.product_id",
        "product_characteristics.characteristic_id",
    ]
    "joins": [
        ["products.ProductId", "sales.ProductId"],
        ["categories.CategoryId", "products.CategoryId"],
        ["products.ProductId", "product_characteristics.product_id"]
    ]
}}
'

### 

# Target Schema:

'
{{
    "catalog": [
    {{
        "column_name": "id",
        "description": "SKU identifier of the product",
        "example": 12355,
        "required": "mandatory",
        "type": "string",
    }},
    {{
        "column_name": "product_name",
        "description": "Name of the product",
        "example": "LG LED 55'",
        "required": "optional",
        "type": "string",
    }},
    {{
        "column_name": "product_description",
        "description": "Free form text of the product description",
        "example": "An LG LED TV 55'",
        "required": "optional",
        "type": "string",
    }},  
    ],
    "transactions: [
    {{
        "column_name": "id",
        "description": "Identifier of the transaction",
        "example": 115,
        "required": "mandatory",
        "type": "string",
    }},
    {{
        "column_name": "product_id",
        "description": "Identifier of the purchased product",
        "example": 16,
        "required": "mandatory",
        "type": "string",
    }},
    {{
        "column_name": "quantity",
        "description": "Number of purchased items",
        "example": 4,
        "required": "mandatory",
        "type": "integer",
    }},
    ]
}}
'

###

# Schema Mapping:
'
{{
    "mappingResult": [
        {{
            "original_table": "products",
            "target_table": "catalog",
            "columns": [
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
                }}
            ]
        }},
        {{
            "original_table": "sales",
            "target_table": "transactions",
            "columns": [
                {{
                    "original_column": "Date",
                    "target_column": "date"
                }},
                {{
                    "original_column": "ProductId",
                    "target_column": "product_id"
                }},
            ],
            "columns_other_tables": [
                {{
                    "original_column": "products.Price",
                    "target_column": "transactions.price"
                }}
            ]
        }},
    ]
}}
'

###

# Query:

'
INSERT INTO target.catalog ('id', 'product_name', 'product_description')
SELECT p.ProductId, p.ProductName, p.ProductDescription
FROM dbo.products as p; 

INSERT INTO target.transactions ('id', 'product_id', 'quantity')
SELECT t.id, t.product_id, t.quantity
FROM dbo.transactions as t;
'

### 

# Answer:

'
INSERT INTO target.catalog ('id', 'product_name', 'product_description')
SELECT p.ProductId, p.ProductName, p.ProductDescription
FROM dbo.products as p;

INSERT INTO target.transactions ('product_id', 'quantity' , 'price')
SELECT s.ProductId, NaN, p.Price
FROM dbo.sales as s
JOIN dbo.products as p
ON s.ProductId = p.ProductId;
'

---> End of examples
"""

TABLE_MAPPING_FEEDBACK_PROMPT = """
*** RETURN ONLY THE GENERATED SQL QUERIES AND NOTHING ELSE ***

Using the example in the system prompt, generate the answer to the following input:

# Tables:

{tables}

###

# Joins:

{joins}

###

# Target Schema:

{target_schema}

###

# Schema Mapping:

{schema_mapping}

### 

# Query:
{queries}

###

# Answer:
"""