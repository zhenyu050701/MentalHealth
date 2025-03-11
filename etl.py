import json
import pandas as pd
from pymongo import MongoClient

class ETLProcessor:
    def __init__(self, mongo_uri, db_name, collection_name, rules_file="transform_rules.json"):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        self.rules = self.load_transform_rules(rules_file)

    def load_transform_rules(self, file_path):
        """ Load transformation rules from JSON file. """
        with open(file_path, "r") as f:
            return json.load(f)

    def extract(self):
        """ Fetch raw data from MongoDB. """
        return list(self.collection.find())

    def transform(self, data):
        """ Apply transformation rules to clean/process data. """
        df = pd.DataFrame(data)
        
        # Example: Apply rules
        for col, operation in self.rules.items():
            if operation == "uppercase":
                df[col] = df[col].str.upper()
            elif operation == "lowercase":
                df[col] = df[col].str.lower()
            elif operation == "drop":
                df.drop(columns=[col], inplace=True, errors="ignore")

        return df

    def load(self, cleaned_data):
        """ Store transformed data back into MongoDB. """
        self.collection.insert_many(cleaned_data.to_dict("records"))

    def run_pipeline(self):
        """ Execute the full ETL process. """
        raw_data = self.extract()
        transformed_data = self.transform(raw_data)
        self.load(transformed_data)
        print("ETL process completed!")

# Example Usage:
if __name__ == "__main__":
    MONGO_URI = "your_mongo_uri"
    DB_NAME = "your_db"
    COLLECTION_NAME = "your_collection"

    etl = ETLProcessor(MONGO_URI, DB_NAME, COLLECTION_NAME)
    etl.run_pipeline()
