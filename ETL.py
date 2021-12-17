import configparser
import psycopg2
from sql_queries import copy_table_queries, insert_table_queries

def load_staging_tables(cur, conn):
    '''
    This function loads log and song data from S3 into staging tables in redshift.
    Args:
        parameter 1 (str): cur - psycopg2 (gives ability execute the PostgreSQL commands within python)
        parameter 2 (str): conn - creates connection to psycopg2 database
    Returns: N/A
    '''
    for query in copy_table_queries:
        cur.execute(query)
        conn.commit()


def insert_tables(cur, conn):
    '''
    This function inserts data into the fact and dimension tables from the staging tables.
    Args:
        parameter 1 (str): cur - psycopg2 (gives ability execute the PostgreSQL commands within python)
        parameter 2 (str): conn - creates connection to psycopg2 database
    Returns: N/A
    '''
    for query in insert_table_queries:
        cur.execute(query)
        conn.commit()


def main():
    '''
    Main function. Evokes load_staging_tables and insert_tables to execute ETL.
    Args: N/A
    Returns: N/A
    '''
    config = configparser.ConfigParser()
    config.read('dwh.cfg')

    conn = psycopg2.connect("host={} dbname={} user={} password={} port={}".format(*config['CLUSTER'].values()))
    cur = conn.cursor()
    
    load_staging_tables(cur, conn)
    insert_tables(cur, conn)

    conn.close()


if __name__ == "__main__":
    main()