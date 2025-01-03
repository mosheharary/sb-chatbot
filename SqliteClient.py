import sqlitecloud
import streamlit as st
import json
import os


class SqliteClient:
    def __init__(self,db_name):
        self.db_name = db_name
        self.sqlite_host=st.secrets["sqlite_host"]
        self.sqlite_port=st.secrets["sqlite_port"]
        self.sqlite_key=st.secrets["sqlite_key"]
        self.sqlitecloud_connection_string=f"sqlitecloud://{self.sqlite_host}:{self.sqlite_port}/{self.db_name}?apikey={self.sqlite_key}"
        self.use_local_file = st.secrets["use_local_file"]
    
    def insert_data(self,data,table_name): 
        if self.use_local_file == "true":
            self.add_local_usage_entry(data,table_name)
            pass
        else:   
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
            #value_set = sorted(set(values), key=values.index)
            #values_list = []
            #values_list.append(value_set)
            values_list = [sorted(values, key=values.index)]
            try:
                conn = sqlitecloud.connect(self.sqlitecloud_connection_string)
                conn.execute(f"USE DATABASE {self.db_name}")
                conn.executemany(insert_query, values_list)
                conn.close()
            except Exception as e:
                st.error(f"Error: {e}")

    def get_data(self,table_name):
        if self.use_local_file == "true":
            return self.load_local_usage_data(table_name)
        else:
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
        if self.use_local_file == "true":
            pass
        else:
            try:
                conn = sqlitecloud.connect(self.sqlitecloud_connection_string)
                conn.execute(f"USE DATABASE {self.db_name}")
                conn.execute(
                    f"CREATE TABLE IF NOT EXISTS {table_name} ({columns})"
                )        
                conn.close()
            except Exception as e:
                st.error(f"Error: {e}")


    def load_local_usage_data(self,table_name):
        USAGE_FILE = f"{table_name}.json"
        if os.path.exists(USAGE_FILE):
            with open(USAGE_FILE, 'r') as f:
                return json.load(f)
        return []

    def save_local_usage_data(self,data,table_name):
        USAGE_FILE = f"{table_name}.json"
        with open(USAGE_FILE, 'w') as f:
            json.dump(data, f)

    def add_local_usage_entry(self,new_data,table_name):
        data = self.load_local_usage_data(table_name)
        data.append(new_data)
        self.save_local_usage_data(data,table_name)
