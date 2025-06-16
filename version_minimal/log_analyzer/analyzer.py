from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf
from pyspark.sql.types import StringType, IntegerType

import re

spark = SparkSession.builder \
    .appName("LogAnalyzerMinimal") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")

lines = spark.readStream.format("socket").option("host", "localhost").option("port", 9999).load()

def extract_status(line):
    match = re.search(r'"GET .* HTTP/1.1" (\d{3})', line)
    return int(match.group(1)) if match else 0

extract_status_udf = udf(extract_status, IntegerType())

logs = lines.withColumn("status", extract_status_udf(col("value")))

errors = logs.filter(col("status") >= 400)

count_errors = errors.groupBy().count()

query = count_errors.writeStream \
    .outputMode("complete") \
    .format("console") \
    .start()

query.awaitTermination()
