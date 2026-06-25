import boto3
import pandas as pd
from io import StringIO

BUCKET = "pfeyass"
FILE_KEY = "faq.csv.csv"

s3 = boto3.client("s3")


def load_dataset():

    obj = s3.get_object(Bucket=BUCKET, Key=FILE_KEY)

    csv_content = obj["Body"].read().decode("utf-8")

    df = pd.read_csv(StringIO(csv_content))

    # نحولو لـ نص منظم باش Claude يفهم
    context = ""

    for _, row in df.iterrows():
        context += f"Question: {row[0]}\nAnswer: {row[1]}\n\n"

    return context