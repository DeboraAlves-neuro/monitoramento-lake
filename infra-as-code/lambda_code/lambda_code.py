'''IMPORTS'''
import base64
import json
import uuid
import math
import boto3
from botocore.exceptions import ClientError

'''IMPORTANT PARAMETERS'''
OFICIAL_OUTPUT_DATABASE = "monitoring_neurolake"
LOG001 = "nl_consumption.log001"
PRD_ACCESS_CREDENTIALS_SECRET = "neurolake/governance/aws_dev/access_keys"

'''AUXILIAR FUNCTIONS'''
def get_uuid():
    uuid_hash = str(uuid.uuid4())
    uuid_hash = '_'.join(uuid_hash.split("-")[:2])
    return uuid_hash

def get_secret_value(secret_name):
    session = boto3.session.Session()
    client = session.client(
        service_name = "secretsmanager",
        region_name = "us-east-1"
    )
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId = secret_name
        )
    except ClientError as e:
        raise e
    if "SecretString" in get_secret_value_response:
        secret = get_secret_value_response["SecretString"]
    else:
        secret = base64.b64decode(get_secret_value_response["SecretBinary"])
    return json.loads(secret)

#listando todas as tabelas dos databases desejados, validando os locations das tabelas e removendo excecoes
def location_existe(table_dict, s3_client):
    location = table_dict["StorageDescriptor"]["Location"]
    if location != '' and location is not None:
        bucket = location.split("/")[2]
        file_key = "".join(location.split("/")[3:]) + "/"
        result = s3_client.list_objects_v2(Bucket = bucket, Prefix = file_key)
        if 'Contents' not in result:
            return False
    else:
        return False
    return True

def locations_existem(table_list):
    s3_client = boto3.client('s3')
    valid_table_list = []
    if location_existe(table_list, s3_client):
        valid_table_list.append(table_list)
    
    return valid_table_list

def padroniza_queries(query_list):
    old_query_list = [query for query in query_list]
    query_list = []
    for query in old_query_list:
        query = ' '.join(s.strip() for s in query.split('\n'))
        query_list.append(query)
    return query_list

def valida_outputs(output_list, permitidos):
    permitidos = [output.split(".")[1] for output in permitidos]
    output_tables = [output.split("/")[-2] for output in output_list]
    repetidos = list(set([x for x in output_tables if output_tables.count(x) > 1]))
    repetidos_nao_permitidos = [output for output in repetidos if output not in permitidos]
    if repetidos_nao_permitidos:
        raise Exception(f"Outputs repetidos: {repetidos_nao_permitidos}")

def listar_databases():
    
    #criando os clients do boto3
    glue_client = boto3.client('glue', region_name = 'us-east-1')

    response = glue_client.get_databases()
    database_list = response['DatabaseList']

    return database_list

def listar_tabelas_database(database_name):

    #criando os clients do boto3
    glue_client = boto3.client('glue', region_name = 'us-east-1')

    #utilizando paginacao para buscar mais de 100 tabelas para cada database
    starting_token = None
    next_page = True
    table_list = []
    while next_page:
        paginator = glue_client.get_paginator(operation_name = "get_tables")
        response_iterator = paginator.paginate(
            DatabaseName = database_name,
            PaginationConfig = {"PageSize": 100, "StartingToken": starting_token},
        )
        for elem in response_iterator:
            table_list += elem["TableList"]
            try:
                starting_token = elem["NextToken"]
            except:
                next_page = False
    print(f"Tabelas do {database_name.upper()}: ", len(table_list))
    return table_list

'''QUESTIONS'''
def tabelas_atualizadas():
    print("#### TABELAS ATUALIZADAS NO LAKE ####")
    
    database_list = listar_databases()
    query_list = []
    output_list = []
    random_hash = get_uuid()
    tabelas_atualizadas = f"sandbox.monitoramento_neurolake_atualizadas{random_hash}"
    databases = ["alfred_logs"]

    query = (f"""
          CREATE TABLE {tabelas_atualizadas} (
                database string,
                tabela string,
                load_date timestamp,
                validade int,
                tabela_atualizada int,
                tabela_desatualizada int,
                uso_60_dias int,
                uso_30_dias int
            )
            ROW FORMAT SERDE 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
            WITH (format='PARQUET', parquet_compression='SNAPPY');
        """)
    query_list.append(query)
    output = f"s3://dev-neurolake-{tabelas_atualizadas.split('.')[0]}/{tabelas_atualizadas.split('.')[1]}/"
    output_list.append(output)

    for database_name in database_list:
        database_dict = database_name["Name"]
        print(database_dict)
        
        if database_dict in databases:
            print(f"ENTROU NO IF!! {database_dict}")
            table_list = listar_tabelas_database(database_dict)
            #ola = locations_existem(table_list)[0]["Name"]
            #print(f"tabelas existentes>> {ola}")
            true_table_list = []
            query = ""
            for table_dict in table_list:
                print(table_dict)
                tabela = locations_existem(table_dict)[0]["Name"]

                query = f"""
                    INSERT INTO {tabelas_atualizadas}
                    SELECT{database_name} AS DATABASE
                    ,{tabela} AS TABLE
                    ,(SELECT MAX(LOAD_DATE) FROM   {database_name}.{tabela})
                    ,60 AS VALIDADE
                    ,case when (SELECT date_diff('day',MAX(LOAD_DATE),CURRENT_DATE) FROM   {database_name}.{tabela}) < 60 
                    then 1 
                    else 0 
                    end as TABELA_ATUALIZADA
                            """
                query_list.append(query)
            if query:
                break
    return query_list
            
    '''MAIN'''
def lambda_handler(event, context):
    # question_list = ["tabelas_atualizadas"]

    # question = event.get("question", None)
    # if question == "tabelas_atualizadas":
    return tabelas_atualizadas()
    


