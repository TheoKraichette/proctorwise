FROM apache/airflow:2.8.0-python3.11

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Docker CLI (version 27.x for API compatibility)
RUN curl -fsSL https://download.docker.com/linux/static/stable/x86_64/docker-27.4.1.tgz | tar xz -C /usr/local/bin --strip-components=1 docker/docker

USER airflow
RUN pip install --no-cache-dir pymysql
