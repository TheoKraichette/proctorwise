FROM apache/spark:3.5.0

USER root

# Download MySQL JDBC driver
RUN curl -o /opt/spark/jars/mysql-connector-j-8.0.33.jar \
    https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/8.0.33/mysql-connector-j-8.0.33.jar

USER spark
