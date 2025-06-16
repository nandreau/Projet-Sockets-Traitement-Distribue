# -*- coding: utf-8 -*-
import os
import json
import re
from dotenv import load_dotenv
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp, window, count, regexp_extract, coalesce, lit, expr, split, when, concat_ws, explode
from pyspark.sql.types import StringType, IntegerType, StructType, StructField


# 1. Charger .env
root_env = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir, '.env'))
load_dotenv(dotenv_path=root_env)
CLIENT_USERNAME = os.getenv("CLIENT_USERNAME")
CLIENT_PASSWORD = os.getenv("CLIENT_PASSWORD")
JKS_PASSWORD    = os.getenv("JKS_PASSWORD")

# Construire le chemin vers le fichier de configuration
config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'kafka_config.json')

# Charger la configuration Kafka
def load_config(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

config = load_config(config_path)

sasl_jaas = (
    'org.apache.kafka.common.security.plain.PlainLoginModule required '
    f'username="{CLIENT_USERNAME}" password="{CLIENT_PASSWORD}";'
)

# Initialiser Spark
spark = SparkSession.builder.appName("KafkaLogAnalyzerWithAlerts").getOrCreate()
spark.sparkContext.setLogLevel("WARN")

# Lire le flux Kafka des logs HTTP avec sécurité TLS + authentification SASL/PLAIN
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", config["bootstrap_servers"]) \
    .option("subscribe", "logs") \
    .option("startingOffsets", "latest") \
    .option("failOnDataLoss", "false") \
    .option("kafka.security.protocol", "SASL_SSL") \
    .option("kafka.ssl.endpoint.identification.algorithm", "") \
    .option("kafka.ssl.truststore.location", config["truststore_location"]) \
    .option("kafka.ssl.truststore.password",  JKS_PASSWORD) \
    .option("kafka.sasl.mechanism", "PLAIN") \
    .option("kafka.sasl.jaas.config", sasl_jaas) \
    .load()

# Extraire la valeur du message en chaîne
lines = df.selectExpr("CAST(value AS STRING)")

# Prétraitement des messages répétés sans UDF
pattern = "(.+) message repeated (\\d+) times: \\[ (.+)\\]"
lines = lines.withColumn("count", coalesce(regexp_extract("value", pattern, 2).cast("int"), lit(1)))
lines = lines.withColumn("dummy", expr("explode(split(repeat('1', count - 1), ''))"))
lines = lines.withColumn("value", when(
    col("value").rlike(pattern),
    concat_ws(" ", regexp_extract("value", pattern, 1), regexp_extract("value", pattern, 3))
).otherwise(col("value"))).drop("dummy", "count")

# Pattern pour parser les logs
log_pattern = re.compile(
    r'(?P<ip>\d+\.\d+\.\d+\.\d+) - - \['
    r'(?P<datetime>[^\]]+)\] "(?P<method>\w+) (?P<url>\S+) HTTP/[0-9.]+" '
    r'(?P<status>\d{3}) (?P<size>\S+) "([^"]*)" "([^"]*)"'
)

def parse_log(line):
    match = log_pattern.match(line)
    if match:
        return match.group("ip"), match.group("url"), int(match.group("status"))
    return "", "", 0

from pyspark.sql.functions import udf
parse_log_udf = udf(parse_log, StructType([
    StructField("ip", StringType()),
    StructField("url", StringType()),
    StructField("status", IntegerType()),
]))

# Appliquer le parsing
parsed_df = lines.select(parse_log_udf(col("value")).alias("parsed")).select("parsed.*")
error_df = parsed_df.filter(col("status") >= 400) \
                    .withColumn("timestamp", current_timestamp())

# Définir le seuil d'alerte
THRESHOLD = 1

alerts = error_df.groupBy(
    window(col("timestamp"), "5 seconds"),
    col("url"),
    col("ip")
).agg(
    count("*").alias("error_count")
).filter(col("error_count") > THRESHOLD)

# Fonction de sauvegarde/affichage des alertes
def write_alerts(batch_df, batch_id):
    if not batch_df.rdd.isEmpty():
        os.makedirs("output/alerts", exist_ok=True)
        with open("output/alerts/alerts.txt", "a", encoding="utf-8") as f:
            for row in batch_df.collect():
                ts = row['window']['start']
                line = f"[{ts}] ALERTE: {row['error_count']} erreurs pour {row['url']} par {row['ip']}"
                print(line)
                f.write(line + "\n")

# Lancer la requête de streaming avec checkpoint
query = alerts.writeStream \
    .option("checkpointLocation", "output/checkpoints") \
    .outputMode("update") \
    .foreachBatch(write_alerts) \
    .start()

print("Analyseur avec alertes en temps réel démarré...")
query.awaitTermination()