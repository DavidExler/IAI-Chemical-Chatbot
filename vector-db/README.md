# Vector DB

We use [Milvus](https://milvus.io/) to store embeddings of the confluence and kit-pages (webcrawler results).
The Chatbot can use these Embeddings for similarity search.
The retreivers in the [backend](../backend/app/retrievers/) will need to be updated accordingly if the vecrot-dbs port is changed here.

## Docker Container

### [Milvus DB](https://milvus.io/)

- **Image**: `milvusdb/milvus`
- **Description**: Milvus is an open-source vector database that provides similar search capability for massive-scale data.
- **Known Issues** removing the version pin of pymilvus or langchain-milvus will result in some easily overlooked errors because of deprecated methods.

### [Attu](https://github.com/zilliztech/attu)

- **Image**: `zilliz/attu`
- **Description**: Attu is a GUI tool for Milvus, which provides a user-friendly interface to interact with Milvus.
- **Port**: `8000`

### [etcd](https://etcd.io/)

- **Image**: `quay.io/coreos/etcd`
- **Description**: etcd is a distributed key-value store that provides a reliable way to store data across a cluster of machines.

### [MinIO](https://min.io/)

- **Image**: `minio/minio`
- **Description**: MinIO is a high-performance object storage server compatible with Amazon S3 APIs.

### initialize-milvus

- **Image**: self-built
- **Description**: A script to initialize Milvus with the required users and privileges.

### import-confluence / import-confluence-private

- **Image**: self-built
- **Description**: A script to import data from Confluence to Milvus.

### import-kit-pages

- **Image**: self-built
- **Description**: A script to import data from Kit Pages to Milvus.

### backup

- **Image**: self-built
- **Description**: A script to backup Milvus data.
