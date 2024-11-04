import sqlitecloud
import streamlit as st
import json


class SqliteClient:
    def __init__(self,db_name):
        self.db_name = db_name
        self.sqlite_host=st.secrets["sqlite_host"]
        self.sqlite_port=st.secrets["sqlite_port"]
        self.sqlite_key=st.secrets["sqlite_key"]
        self.sqlitecloud_connection_string=f"sqlitecloud://{self.sqlite_host}:{self.sqlite_port}/{self.db_name}?apikey={self.sqlite_key}"
        # self.conn = sqlitecloud.connect(self.sqlitecloud_connection_string)
        # self.conn.execute(f"USE DATABASE {self.db_name}")
    
    def insert_data(self,data,table_name):    
        insert_query = f"INSERT INTO {table_name} "    
        values=[]
        keys_str_list = []
        for key , value in data.items():
            values.append(value)
            keys_str_list.append(key)
        
        keys_str = ",".join(keys_str_list)
        insert_keys_str = f"({keys_str})"
        insert_query += insert_keys_str
        insert_query += " VALUES ("
        insert_values_str = ",".join(['?'] * len(data))
        insert_query += insert_values_str
        insert_query += ")"
        value_set = sorted(set(values), key=values.index)
        values_list = []
        values_list.append(value_set)
        try:
            conn = sqlitecloud.connect(self.sqlitecloud_connection_string)
            conn.execute(f"USE DATABASE {self.db_name}")
            conn.executemany(insert_query, values_list)
            conn.close()
        except Exception as e:
            st.error(f"Error: {e}")

    def get_data(self,table_name):
        try:
            conn = sqlitecloud.connect(self.sqlitecloud_connection_string)
            conn.execute(f"USE DATABASE {self.db_name}")
            cursor = conn.execute(f"SELECT * FROM {table_name}")
            result = cursor.fetchone()
            columns = [column[0] for column in cursor.description]
            data = [dict(zip(columns, result))]
            for row in cursor:
                data.append(dict(zip(columns, row)))
            conn.close()                
            return data
            
        except Exception as e:
            st.error(f"Error: {e}")

    def create_table(self,table_name,columns):
        try:
            conn = sqlitecloud.connect(self.sqlitecloud_connection_string)
            conn.execute(f"USE DATABASE {self.db_name}")
            conn.execute(
                f"CREATE TABLE IF NOT EXISTS {table_name} ({columns})"
            )        
            conn.close()
        except Exception as e:
            st.error(f"Error: {e}")
