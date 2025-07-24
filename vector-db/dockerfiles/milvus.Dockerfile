#FROM milvusdb/milvus:v2.2.11
FROM milvusdb/milvus:v2.4.10
RUN curl -L https://github.com/a8m/envsubst/releases/download/v1.4.2/envsubst-"$(uname -s)"-"$(uname -m)" -o envsubst && chmod +x envsubst && mv envsubst /usr/local/bin

COPY configs/milvus.tmpl.yaml /milvus/configs/milvus.tmpl.yaml
#COPY import_confluence.py /import_confluence.py

ENTRYPOINT ["/bin/bash", "-c", "envsubst < /milvus/configs/milvus.tmpl.yaml > /milvus/configs/milvus.yaml && milvus run standalone"]
