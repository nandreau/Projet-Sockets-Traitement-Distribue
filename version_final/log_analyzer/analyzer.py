from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf
from pyspark.sql.types import IntegerType
import re
import os
os.environ["HADOOP_USER_NAME"] = "test"


# Crée la SparkSession avec le connecteur Kafka
spark = SparkSession.builder \
    .appName("KafkaLogAnalyzer") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")

# Lire depuis le topic Kafka
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "http-logs") \
    .option("startingOffsets", "latest") \
    .load()

# Kafka retourne les messages sous forme de bytes → décoder
lines = df.selectExpr("CAST(value AS STRING)").alias("logline")

# Fonction pour extraire le code HTTP
def extract_status(line):
    match = re.search(r'"GET .* HTTP/1.1" (\d{3})', line)
    return int(match.group(1)) if match else 0

extract_status_udf = udf(extract_status, IntegerType())

logs = lines.withColumn("status", extract_status_udf(col("value")))

# Garder uniquement les erreurs HTTP >= 400
errors = logs.filter(col("status") >= 400)

# Regrouper et compter les erreurs
error_counts = errors.groupBy("status").count()

# Affichage console en streaming
query = error_counts.writeStream \
    .outputMode("complete") \
    .format("console") \
    .option("truncate", False) \
    .start()

query.awaitTermination()
