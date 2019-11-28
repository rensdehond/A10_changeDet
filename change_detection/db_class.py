import logging
import psycopg2
import sys
import json


class Database:
    """
    Class die database kan aanroepen.

    Gebruik Database('metis') om een database te maken.
    ipv metis kan etl_02, etl_03, localhost of metis (als string)

    """

    def __init__(self, db,  host='', dbname='', user='', password='', port=5432):
        self.database_name = db

        if db.lower() in ('metis', 'etl_02', 'etl_03', 'localhost'):
            eval('self.connect_{}()'.format(db.lower()))
           
        else:
            assert '' not in (host, self.database_name, user, password, port), 'no default database and empty argument found.'
            self.connect(host,dbname,user,password,port)


    def connect(self, host, dbname, user, password, port=5432):
        self.database_name = dbname
        try:
            self.database_connection = psycopg2.connect(
                host=host, database=dbname,
                user=user, password=password,
                connect_timeout=3)
            # return database_connection  # .set_client_encoding('utf-8')
        except psycopg2.OperationalError as e:
            logging.error('Unable to connect: {}'.format(e))
            sys.exit(1)

    def execute_query(self, query, query_parameters=None):
        """
        Functie om de database connecties uit connect_databases.py te gebruiken om informatie op te vragen of wijzigingen
        te doen in de database.
        Benodigde input is de database connectie van de bonvengenoemde functie, die in het voorbeeld in een dictionary staat
        en een query op de in de functie ingevoerde database. Optioneel zijn andere parameters
        die psycopg2 accepteerd, zie:
        http://initd.org/psycopg/docs/usage.html
        http://initd.org/psycopg/docs/cursor.html
        """
        from psycopg2.extras import DictCursor

        try:
            # Following http://initd.org/psycopg/docs/faq.html#best-practices
            # And https://stackoverflow.com/questions/21158033/query-from-postgresql-using-python-as-dictionary#21158697
            with self.database_connection.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query, query_parameters)
                try:
                    results = [dict(row) for row in cursor]
                # no records have returned
                except psycopg2.ProgrammingError:
                    results = []
                self.database_connection.commit()
        except Exception as e:
            logging.error(
                f'Error: {e}, \ndatabase: {self.database_name}, \nquery: {query}, \nparameters: {query_parameters}')
            self.database_connection.rollback()
            error = {
                'response_json': json.dumps({'error': {'response_code': '400', 'reason': str(e)}}),
                'status_code': 400
            }
            return None, error
        return results, None
