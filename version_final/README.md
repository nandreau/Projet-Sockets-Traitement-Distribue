# Projet d'analyse de logs HTTP en temps réel – Chaussettes.io

Ce projet propose un système d’analyse **en temps réel** des logs HTTP pour **Chaussettes.io**, entreprise spécialisée dans la vente de chaussettes personnalisées.

Il s’appuie sur :
- **Kafka** pour la transmission des événements
- **Spark Structured Streaming** pour leur traitement
- Une génération de logs simulés configurable

## 🧭 Objectifs

- 🔄 Lire les logs depuis Kafka (`http-logs`)
- 🚨 Déclencher des alertes sur comportement anormal (ex. >5 erreurs HTTP en <5 sec)
- 📊 Générer des métriques utiles (fréquence d’erreurs par IP/URL)
- 🔐 Intégrer les bases de la sécurité dans l’architecture
- 🔁 Automatiser l’infrastructure (Docker, scripts)

## 📁 Structure du projet

```text
project-root/
├── .env                        # variables d’environnement (ex. chemins, credentials)
├── .gitignore                  # règles d’exclusion Git
├── bin/                        # utilitaires Hadoop (winutils, etc.)
├── certs/                      # certificats CA + keystore/truststore
├── config/
│   ├── kafka_config.json       # configuration Kafka (générée depuis template)
│   └── log4j.properties        # configuration Log4j pour Spark
├── logs/
│   └── generator.log           # historique complet des logs simulés
├── output/
│   ├── alerts/                 # alertes détectées (alerts.txt)
│   └── checkpoints/            # Répertoire des points de reprise de Spark Structured Streaming
├── src/
│   ├── log_generator_kafka.py  # script de génération et envoi de logs
│   └── log_analyzer_kafka.py   # application Spark Structured Streaming
├── docker-compose.yml          # services Zookeeper + Kafka sécurisés
├── requirements.txt            # dépendances Python
└── README.md                   # documentation du projet
```

## ✅ Prérequis

### Configurer l’environnement

```powershell
$env:HADOOP_HOME = "$(Get-Location)"
$env:PATH = "$($env:HADOOP_HOME)\bin;$env:PATH"
$env:PYSPARK_PYTHON="C:\path\to\python.exe"
$env:PYSPARK_DRIVER_PYTHON="C:\path\to\python.exe"
```
### Creer les Variables d’environnement

Créez un fichier `.env` à la racine (non versionné) :

```
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin-secret
CLIENT_USERNAME=client
CLIENT_PASSWORD=client-secret
JKS_PASSWORD=password1234
```
---

### Ajouter les Certificats et sécurité

```powershell
Get-Content .env |
  ForEach-Object {
    if ($_ -and $_ -notmatch '^\s*#') {
      $kv = $_ -split '=', 2
      Set-Item -Path "Env:\$($kv[0])" -Value $kv[1]
    }
  }
openssl genrsa -out certs/ca-key.pem 2048
openssl req -x509 -new -nodes -key certs/ca-key.pem -sha256 -days 365 -out certs/ca-cert.pem -subj "//CN=Chaussettes.io Root CA"
keytool -genkeypair -alias kafka-broker -keyalg RSA -keystore certs/kafka.server.keystore.jks -storepass $Env:JKS_PASSWORD -keypass $Env:JKS_PASSWORD -validity 365 -dname "CN=localhost,OU=IT,O=Chaussettes.io,L=Paris,ST=IDF,C=FR"
keytool -certreq -alias kafka-broker -keystore certs/kafka.server.keystore.jks -file certs/kafka-broker.csr -storepass $Env:JKS_PASSWORD
openssl x509 -req -in certs/kafka-broker.csr -CA certs/ca-cert.pem -CAkey certs/ca-key.pem -CAcreateserial -out certs/kafka-broker-signed.pem -days 365 -sha256
keytool -importcert -alias CARoot -file certs/ca-cert.pem -keystore certs/kafka.server.keystore.jks -storepass $Env:JKS_PASSWORD -noprompt
keytool -importcert -alias kafka-broker -file certs/kafka-broker-signed.pem -keystore certs/kafka.server.keystore.jks -storepass $Env:JKS_PASSWORD
keytool -importcert -alias CARoot -file certs/ca-cert.pem -keystore certs/kafka.client.truststore.jks -storepass $Env:JKS_PASSWORD -noprompt
```

## 🚀 Exécution

### 1. Démarrer Kafka et Zookeeper

```powershell
docker-compose -f docker-compose.yml up -d --build
```

### 2. Lancer le générateur de logs

```powershell
python src/log_generator_kafka.py --mode kafka --rate 3 --error-rate 0.5
```

### 3. Démarrer l’analyseur Spark

```powershell
spark-submit `
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 `
  --conf "spark.driver.extraJavaOptions=-Dlog4j.configuration=file:config/log4j.properties" `
  src/log_analyzer_kafka.py
```

Et voilà une interface web Spark UI est disponible sur http://localhost:4040/ pour suivre en temps réel vos jobs et voir les métriques d’exécution !

## 📈 Fonctionnalités implémentées

- Génération de logs HTTP personnalisable via arguments
- Transmission sécurisée (SASL_SSL) vers Kafka
- Analyse en streaming avec Spark (détection d’erreurs)
- Alertes persistantes et console