#!/bin/bash

LIMITE_MINUTOS=30
CONTAINER="mqtt_handler"

while true; do
  echo "[INFO] Verificando último dado no banco de dados..."
  ULTIMO=$(mariadb --skip-ssl -h mysql-database -u root -pexample -D weather_data -se "SELECT MAX(timestamp) FROM sensor_data")
  
  if [ -z "$ULTIMO" ]; then
    echo "[WARN] Nenhum dado encontrado no banco."
  else
    AGORA=$(date +%s)
    DIFERENCA=$(( (AGORA - ${ULTIMO%.*}) / 60 ))

    echo "[INFO] Último dado: $DIFERENCA minutos atrás"

    if [ "$DIFERENCA" -gt "$LIMITE_MINUTOS" ]; then
      echo "[ALERTA] Dados estagnados! Reiniciando container $CONTAINER..."
      docker restart $CONTAINER
    else
      echo "[OK] Dados recentes. Nenhuma ação necessária."
    fi
  fi

  sleep 300  # Espera 5 minutos
done
