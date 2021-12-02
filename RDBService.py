import pymysql

from context import get_db_info

class RDBService:
    '''
        handles database queries
    '''

    @classmethod
    def get_db_connection(cls):
        db_info = get_db_info()

        connection = pymysql.connect(
            host=db_info["host"],
            user=db_info["user"],
            password=db_info["password"],
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )
        return connection

    @classmethod
    def run_sql(cls, sql_stmt):
        print(sql_stmt)
        connection = RDBService.get_db_connection()
        cursor = connection.cursor()
        cursor.execute(sql_stmt)
        result = cursor.fetchall()
        return result

    @classmethod
    def run_sql_create_and_get_id(cls, sql_stmt):
        print(sql_stmt)
        connection = RDBService.get_db_connection()
        cursor = connection.cursor()
        cursor.execute(sql_stmt)
        created_row_id = cursor.lastrowid
        return created_row_id
    
    @classmethod
    def get_where_clause_from_template(cls, template):
        '''
            {'a': 1, 'b': 'text'} => "a = 1 and b = 'text'"
            {'c': ['d','e']} => "c in ('d', 'e')"
        '''
        if len(template) == 0:
            return ""
        
        where_clause = "where "
        for k, v in template.items():
            if isinstance(v, str):
                where_clause += f"{k} = '{v}' and "
            elif isinstance(v, list):
                where_clause += f"""{k} in ({", ".join([f"'{i}'" for i in v])}) and """
            else:
                where_clause += f"{k} = {v} and "
        where_clause = where_clause.rstrip(' and ')

        return where_clause

    @classmethod
    def get_set_clause_from_dict(cls, dict_data):
        '''
            {'a': 1, 'b': 'text'} => "a = 1 and b = 'text'"
        '''
        assert(len(dict_data) >= 1)
        
        set_clause = ""
        for k, v in dict_data.items():
            if isinstance(v, str):
                set_clause += f"{k} = '{v}', "
            else:
                set_clause += f"{k} = {v}, "
        set_clause = set_clause.rstrip(', ')

        return set_clause

    @classmethod
    def find_by_template(cls, db_name, table_name, template, field_list=None):
        equi_clause = cls.get_where_clause_from_template(template)
        field_clause = ", ".join(field_list) if field_list else "*"
        sql_stmt = f"select {field_clause} from {db_name}.{table_name} {equi_clause}"
        result = RDBService.run_sql(sql_stmt)
        return result

    @classmethod
    def create(cls, db_name, table_name, row_data):
        '''
            insert a new row into table
        '''
        columns = ', '.join(list(row_data.keys()))
        values = ', '.join([f"'{v}'" for v in list(row_data.values())])
        sql_stmt = f"insert into {db_name}.{table_name} ({columns}) values ({values})"
        created_row_id = cls.run_sql_create_and_get_id(sql_stmt)
        return created_row_id

    @classmethod
    def update(cls, db_name, table_name, template, new_data):
        '''
            update a row that matches template with new data
        '''
        set_clause = cls.get_set_clause_from_dict(new_data)
        where_clause = cls.get_where_clause_from_template(template)
        sql_stmt = f"update {db_name}.{table_name} set {set_clause} {where_clause}"
        cls.run_sql(sql_stmt)

    @classmethod
    def delete(cls, db_name, table_name, template):
        where_clause = cls.get_where_clause_from_template(template)
        sql_stmt = f"delete from {db_name}.{table_name} {where_clause}"
        cls.run_sql(sql_stmt)

