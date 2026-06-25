import boto3
import pandas as pd
from io import StringIO

BUCKET = "entreprise-agent-data"   # ← بدلها
FILE_KEY = "dataset.csv"           # ← بدلها

s3 = boto3.client("s3")


def load_dataset():

    obj = s3.get_object(Bucket=BUCKET, Key=FILE_KEY)

    content = obj["Body"].read().decode("utf-8")

    df = pd.read_csv(StringIO(content))

    # نحولو النص باش يتعطى للـ LLM
    text_data = df.to_string(index=False)

    return text_data
