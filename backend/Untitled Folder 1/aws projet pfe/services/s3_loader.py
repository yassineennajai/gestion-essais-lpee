import boto3
import pandas as pd
from io import StringIO
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)

def load_data():
    """
    Load Sales dataset + FAQ dataset from S3
    Returns dictionary:
    {
        "sales": DataFrame,
        "faq": DataFrame
    }
    """
    
    s3 = boto3.client("s3")
    
  
    bucket = "enterprise-ai-bucket-data"
    
    files = {
        "sales": "Supermarket Sales Cleaned.csv",
        "faq": "faq.csv.csv"
    }
    
    data = {}

    for name, key in files.items():
        try:
            logger.info(f"Loading {name} from {key}...")
            
            obj = s3.get_object(Bucket=bucket, Key=key)
            
            df = pd.read_csv(
                StringIO(obj["Body"].read().decode("utf-8"))
            )
            
            data[name] = df
            
            logger.info(f"{name} loaded successfully. Shape: {df.shape}")
        
        except ClientError as e:
            logger.error(f"Error loading {key}: {e}")
            data[name] = None

    return data
