from datetime import datetime, timedelta

def cluster_metrics():
    print("#### Cluster Metrics ####")
    now = datetime.now()
    current_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    lower_boundary = now - timedelta(days=5)
    year_month = now.strftime("%Y%m")

    now = now.strftime("%Y-%m-%d %H:%M:%S")
    current_month = current_month.strftime("%Y-%m-%d %H:%M:%S")
    lower_boundary = lower_boundary.strftime("%Y-%m-%d %H:%M:%S")

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

    return query, output_table

