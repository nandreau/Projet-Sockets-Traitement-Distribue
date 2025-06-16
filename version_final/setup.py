from kafka.admin import KafkaAdminClient, NewTopic

admin_client = KafkaAdminClient(bootstrap_servers="localhost:9092")

topic_list = [NewTopic(name="http-logs", num_partitions=1, replication_factor=1)]
try:
    admin_client.create_topics(new_topics=topic_list, validate_only=False)
    print("Topic 'http-logs' créé.")
except Exception as e:
    print(f"Erreur ou topic déjà existant: {e}")
