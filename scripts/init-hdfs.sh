#!/bin/bash
# Script d'initialisation de la structure HDFS pour ProctorWise

echo "Creating HDFS directory structure..."

docker exec proctorwise-namenode hdfs dfs -mkdir -p /proctorwise/raw/frames
docker exec proctorwise-namenode hdfs dfs -mkdir -p /proctorwise/raw/recordings
docker exec proctorwise-namenode hdfs dfs -mkdir -p /proctorwise/processed/anomaly_reports
docker exec proctorwise-namenode hdfs dfs -mkdir -p /proctorwise/processed/grading_results
docker exec proctorwise-namenode hdfs dfs -mkdir -p /proctorwise/processed/user_performance
docker exec proctorwise-namenode hdfs dfs -mkdir -p /proctorwise/ml/models
docker exec proctorwise-namenode hdfs dfs -mkdir -p /proctorwise/archive
docker exec proctorwise-namenode hdfs dfs -chmod -R 777 /proctorwise

echo "HDFS structure created successfully!"
docker exec proctorwise-namenode hdfs dfs -ls -R /proctorwise
