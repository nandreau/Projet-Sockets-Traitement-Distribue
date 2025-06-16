# Version complete 
## Lancer le serveur socket : 
python3 log_generator/socket_server.py
## Lancer le compteur d'erreur : 
spark-submit log_analyzer/analyzer.py

## Paramètre du script log_generator : 
| Paramètre CLI       | Type    | Par défaut             | Description                                                                                                                                              |
| ------------------- | ------- | ---------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--rate`            | `int`   | `1`                    | Nombre de logs générés **par seconde**. <br>➡️ `--rate 5` génère 5 logs/sec                                                                              |
| `--error-rate`      | `float` | `0.2`                  | Pourcentage de logs qui sont des erreurs, **si l’IP ou l’URL est concernée**. <br>➡️ `--error-rate 0.5` = 50% de chances d’erreur pour IP/URL "à risque" |
| `--error-codes`     | `int+`  | `[404, 500, 401, 403]` | Liste des codes HTTP considérés comme erreurs.                                                                                                           |
| `--ok-codes`        | `int+`  | `[200]`                | Liste des codes HTTP de succès.                                                                                                                          |
| `--error-url-ratio` | `float` | `0.4`                  | Part des URLs (ex: `/login`, `/cart`) qui sont susceptibles de produire des erreurs. <br>➡️ `--error-url-ratio 0.4` = 40% des URLs sont "problématiques" |
| `--error-ip-ratio`  | `float` | `0.4`                  | Même principe mais pour les IPs (utilisateurs).                                                                                                          |
| `--host`            | `str`   | `"localhost"`          | Hôte où démarrer le serveur socket. Laisse `"localhost"` pour tester localement.                                                                         |
| `--port`            | `int`   | `9999`                 | Port utilisé pour la socket. Correspond à celui utilisé dans `analyzer.py`.                                                                              |
| `--kafka`           | `bool`  | `False`                | Active l’envoi des logs vers Kafka au lieu de la socket. <br>➡️ `--kafka` envoie les logs sur le topic `http-logs` via `localhost:9092`.                 |
