"""IMPORTS"""
import base64
import json
import uuid
import math
import boto3
import re
from botocore.exceptions import ClientError
from datetime import datetime, timedelta

"""IMPORTANT PARAMETERS"""
OFICIAL_OUTPUT_DATABASE = "monitoring_neurolake"
LOG001 = "nl_consumption.log001"
PRD_ACCESS_CREDENTIALS_SECRET = "neurolake/governance/aws_dev/access_keys"

"""AUXILIAR FUNCTIONS"""


def get_uuid():
    uuid_hash = str(uuid.uuid4())
    uuid_hash = "_".join(uuid_hash.split("-")[:2])
    return uuid_hash


def get_secret_value(secret_name):
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name="us-east-1")
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        raise e
    if "SecretString" in get_secret_value_response:
        secret = get_secret_value_response["SecretString"]
    else:
        secret = base64.b64decode(get_secret_value_response["SecretBinary"])
    return json.loads(secret)


# listando todas as tabelas dos databases desejados, validando os locations das tabelas e removendo excecoes
def location_existe(table_dict, s3_client):
    # print(table_dict)
    location = table_dict["StorageDescriptor"]["Location"]
    if location != "" and location is not None:
        bucket = location.split("/")[2]
        file_key = "".join(location.split("/")[3:]) + "/"
        result = s3_client.list_objects_v2(Bucket=bucket, Prefix=file_key)
        if "Contents" not in result:
            return False
    else:
        return False
    return True


def locations_existem(table_list):
    s3_client = boto3.client("s3")
    valid_table_list = []
    for table_dict in table_list:
        if location_existe(table_dict, s3_client):
            valid_table_list.append(table_dict)

    return valid_table_list


def padroniza_queries(query_list):
    old_query_list = [query for query in query_list]
    query_list = []
    for query in old_query_list:
        query = " ".join(s.strip() for s in query.split("\n"))
        query_list.append(query)
    return query_list


def valida_outputs(output_list, permitidos):
    permitidos = [output.split(".")[1] for output in permitidos]
    output_tables = [output.split("/")[-2] for output in output_list]
    repetidos = list(set([x for x in output_tables if output_tables.count(x) > 1]))
    repetidos_nao_permitidos = [
        output for output in repetidos if output not in permitidos
    ]
    if repetidos_nao_permitidos:
        raise Exception(f"Outputs repetidos: {repetidos_nao_permitidos}")


def listar_databases():
    # criando os clients do boto3
    glue_client = boto3.client("glue", region_name="us-east-1")

    response = glue_client.get_databases()
    database_list = response["DatabaseList"]

    return database_list


def listar_tabelas_database(database_name):
    # criando os clients do boto3
    glue_client = boto3.client("glue", region_name="us-east-1")

    # utilizando paginacao para buscar mais de 100 tabelas para cada database
    starting_token = None
    next_page = True
    table_list = []
    while next_page:
        paginator = glue_client.get_paginator(operation_name="get_tables")
        response_iterator = paginator.paginate(
            DatabaseName=database_name,
            PaginationConfig={"PageSize": 100, "StartingToken": starting_token},
        )
        for elem in response_iterator:
            table_list += elem["TableList"]
            try:
                starting_token = elem["NextToken"]
            except:
                next_page = False
    print(f"Tabelas do {database_name.upper()}: ", len(table_list))
    return table_list

def listar_ultimas_versoes_tabelas(database_name):
    # Obtendo a lista completa de tabelas usando a função existente
    table_list = listar_tabelas_database(database_name)

    last_versions = {}
    version_pattern = re.compile(r'v(\d+)')

    for table in table_list:
        table_name = table["Name"]
        match = re.match(r'(.+)_v(\d+)', table_name)
        if match:
            table_base_name, version = match.groups()
            version = int(version)
            if table_base_name not in last_versions or version > last_versions[table_base_name]["version"]:
                last_versions[table_base_name] = {"version": version, "table": table}

    final_table_list = [info["table"] for info in last_versions.values()]
    return final_table_list

# ultimas_versoes = listar_ultimas_versoes_tabelas("consumption")
# print(f"Tabelas e suas últimas versões: {ultimas_versoes}")


"""QUESTIONS"""

def tabelas_atualizadas():
    print("#### TABELAS ATUALIZADAS NO LAKE ####")

    database_list = listar_databases()
    query_list = []
    output_list = []
    random_hash = get_uuid()
    tabelas_atualizadas = f"sandbox.monitoramento_neurolake_atualizadas_{random_hash}"
    databases = ["consumption"]

    query = f"""
          CREATE TABLE {tabelas_atualizadas} (
                DATABASE string,
                TABLE string,
                LOAD_DATE timestamp,
                VALIDADE int,
                TABELA_ATUALIZADA int,
                TABELA_DESATUALIZADA int,
                USO_60_DIAS int,
                USO_30_DIAS int
            )
            ROW FORMAT SERDE 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
            WITH (format='PARQUET', parquet_compression='SNAPPY');
        """
    query_list.append(query)
    output = f"s3://dev-neurolake-{tabelas_atualizadas.split('.')[0]}/{tabelas_atualizadas.split('.')[1]}/"
    output_list.append(output)

    for database in database_list:
        database_name = database["Name"]
        if database_name in databases:
            print(f"Databases listados > {database_name}")
            table_list = listar_ultimas_versoes_tabelas(database_name)
            # lista_tabelas = locations_existem(table_list)
            # print(f"tabelas existentes >> {lista_tabelas}")
            query = ""
            for table_dict in table_list:

                query = f"""
                    INSERT INTO {tabelas_atualizadas}
                        SELECT
                             {database_name} AS DATABASE
                            ,{table_dict["Name"]} AS TABLE
                            ,(SELECT MAX(LOAD_DATE) FROM   {database_name}.{table_dict["Name"]})
                            ,60 AS VALIDADE,
                        CASE WHEN (SELECT date_diff('day',MAX(LOAD_DATE),CURRENT_DATE) FROM   {database_name}.{table_dict["Name"]})
                            ,60 AS VALIDADE) < 60
                            then 1
                            else 0
                            end as TABELA_ATUALIZADA
                """
                query_list.append(query)
    return query_list

def cluster_metrics():
    print("#### Cluster Metrics ####")
    now = datetime.now()
    current_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    lower_boundary = now - timedelta(days=5)
    year_month = now.strftime("%Y%m")

    now = now.strftime("%Y-%m-%d %H:%M:%S")
    current_month = current_month.strftime("%Y-%m-%d %H:%M:%S")
    lower_boundary = lower_boundary.strftime("%Y-%m-%d %H:%M:%S")

    query_list = []

    database = 'governanca_dados_prd'
    table = 'UTILIZACAO_DE_CLUSTERS'
    output_table = 'sandbox.monitoramento_neurolake_clusters_metrics_{now}'

    query = f"""
        CREATE TABLE {output_table} WITH (format='PARQUET', parquet_compression='SNAPPY') AS
            SELECT
                a.SQUAD,
                ROUND(COUNT(*) * 3 / 60, 1) AS HORAS_USADAS_ULTIMOS_5_DIAS,
                ROUND((COUNT(CASE WHEN a.percentual_de_utilizacao > 0 THEN 1 END) * 3 / 60) / 5, 1) AS MEDIA_HORAS_ULTIMOS_5_DIAS,
                b.HORAS_ACUMULADAS_MES,
                '{year_month}' AS YEARMONTH
            FROM {database}.{table} a
            LEFT JOIN (
                SELECT SQUAD, (ROUND(COUNT(*) * 3 / 60,1))  AS HORAS_ACUMULADAS_MES
                FROM {database}.{table} WHERE datahora >= TIMESTAMP '{current_month}' GROUP BY SQUAD
            ) as b ON a.SQUAD = b.SQUAD
            WHERE a.datahora >= TIMESTAMP '{lower_boundary}' AND a.percentual_de_utilizacao > 0
            GROUP BY a.SQUAD
            ORDER BY HORAS_USADAS_ULTIMOS_5_DIAS DESC
    """
    query_list.append(query)
    return query, output_table


    """MAIN"""

def lambda_handler(event, context):
    question_list = ["tabelas_atualizadas", "cluster_metrics"]
    question = event.get("question", None)
    if question == "tabelas_atualizadas":
        return tabelas_atualizadas()
    elif question == "cluster_metrics":
        return cluster_metrics()