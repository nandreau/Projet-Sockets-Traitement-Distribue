## Lancer Zookeeper et Kafka
docker compose -f kafka-compose.yml up -d

## Verifier que les containers tournent : 
docker ps

## Initialiser le topic http-logs 
python setup.py

## Verifier l'existence du topic http-logs : 
docker exec -it $(docker ps --filter name=kafka --format "{{.ID}}") bash 

kafka-topics --list --bootstrap-server localhost:9092

## Lancer le générateur de logs :
python log_generator.py --mode kafka --rate 3 --error-rate 0.5

## Lancer le script d'analyse : 
spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 analyzer.py