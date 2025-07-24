import logging
import os

from pymilvus import MilvusClient
from pymilvus.exceptions import MilvusException

host = os.environ.get("MILVUS_HOST", "127.0.0.1")
port = os.environ.get("MILVUS_PORT", "19530")
user = os.environ.get("MILVUS_ROOT_USER", "root")
password = os.environ.get("MILVUS_ROOT_PASSWORD", "Milvus")

readonly_role = os.environ.get("MILVUS_READONLY_ROLE", "readonly_role")
readonly_user = os.environ.get("MILVUS_READONLY_USER", "readonly_user")
readonly_password = os.environ.get("MILVUS_READONLY_PASSWORD")

logger = logging.getLogger(__name__)


def main():
    # 1. Create a milvus client
    logger.info("Connecting to Milvus")
    client = MilvusClient(
        uri=f"http://{host}:{port}",
        user=user,
        password=password,
    )

    # 2. Create a role
    logger.info(f"Creating role: {readonly_role}")
    try:
        client.create_role(role_name=readonly_role)
    except MilvusException as e:
        logger.warning(f"Cannot create role {readonly_role}: {e}")

    # 3. Create a user
    logger.info(f"Creating user: {readonly_user}")
    try:
        client.create_user(readonly_user, readonly_password)
    except MilvusException as e:
        logger.warning(f"Cannot create user {readonly_user}: {e}")

    # 4. Add user to role
    logger.info(f"Adding user {readonly_user} to role {readonly_role}")
    try:
        client.grant_role(readonly_user, readonly_role)
    except MilvusException as e:
        logger.warning(f"Cannot add user {readonly_user} to role {readonly_role}: {e}")

    # 5. Grant privilege to role Global
    logger.info(f"Granting global privileges to role {readonly_role}")
    priviledges = [
        "DescribeCollection",
        "ListResourceGroups",
        "DescribeResourceGroup",
        "DescribeAlias",
        "ListDatabases",
        "ShowCollections",
    ]
    for privilege in priviledges:
        try:
            client.grant_privilege(
                role_name=readonly_role,
                object_type="Global",
                privilege=privilege,
                object_name="*",
            )
        except MilvusException as e:
            logger.warning(
                f"Cannot grant global privilege {privilege} to role {readonly_role}: {e}"
            )

    # 6. Grant privilege to role collection
    logger.info(f"Granting collection privileges to role {readonly_role}")
    priviledges = [
        "IndexDetail",
        "GetLoadingProgress",
        "GetLoadState",
        "Search",
        "GetFlushState",
        "Query",
        "GetStatistics",
        "ShowPartitions",
        "HasPartition",
    ]
    for privilege in priviledges:
        try:
            client.grant_privilege(
                role_name=readonly_role,
                object_type="Collection",
                privilege=privilege,
                object_name="*",
            )
        except MilvusException as e:
            logger.warning(
                f"Cannot grant collection privilege {privilege} to role {readonly_role}: {e}"
            )


if __name__ == "__main__":
    main()
