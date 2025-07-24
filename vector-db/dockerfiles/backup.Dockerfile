FROM debian

RUN apt-get update && \
    apt-get install --no-install-recommends -y wget curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN wget -q https://github.com/zilliztech/milvus-backup/releases/download/v0.4.12/milvus-backup_Linux_x86_64.tar.gz && \
    tar -zxvf milvus-backup_Linux_x86_64.tar.gz && \
    mv milvus-backup /usr/local/bin/ && \
    rm -rf milvus-backup_Linux_x86_64.tar.gz

RUN wget -q https://github.com/a8m/envsubst/releases/download/v1.4.2/envsubst-"$(uname -s)"-"$(uname -m)" -O /usr/local/bin/envsubst && \
    chmod +x /usr/local/bin/envsubst

COPY configs/milvus-backup.tmpl.yaml /backup.tmpl.yaml
