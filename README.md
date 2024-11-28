# 💬 Chatbot template

A simple Streamlit app that shows how to build a chatbot using OpenAI's GPT-3.5.

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://chatbot-template.streamlit.app/)

### How to run it on your own machine

1. Install the requirements

   ```
   $ pip install -r requirements.txt
   ```

2. Run the app

   ```
   $ streamlit run streamlit_app.py
   ```

3. Secrets to use in application:
```
OPENAI_API_KEY = "xxxxxxxxxxxxxxxxxxxxxxx"
PINECONE_API_KEY = "xxxxxxxxxxxxxxxxxxxxxxx"
JSONBIN_KEY = "xxxxxxxxxxxxxxxxxxxxxxx"   (https://jsonbin.io/)
gcs_bucket_name = "xxxxxxxxxxxxxxxxxxxxxxx"
auth_username = "xxxxxxxxxxxxxxxxxxxxxxx"
auth_password = "xxxxxxxxxxxxxxxxxxxxxxx"

sqldb = "sqlitecloud" (https://dashboard.sqlitecloud.io/)
sqlite_host="xxxxxxxxxxxxxxxxxxxxxxx"
sqlite_port="xxxxxxxxxxxxxxxxxxxxxxx"
sqlite_key="xxxxxxxxxxxxxxxxxxxxxxx"
use_local_file = "false"

[gcp_service_account]
type = "service_account"
project_id = "xxxxxxxxxxxxxxxxxxxxxxx"
private_key_id = "xxxxxxxxxxxxxxxxxxxxxxx"
private_key = "xxxxxxxxxxxxxxxxxxxxxxx"
client_email = "xxxxxxxxxxxxxxxxxxxxxxx@xxxxxxxxxxxxxxxxxxxxxxx.iam.gserviceaccount.com"
client_id = "xxxxxxxxxxxxxxxxxxxxxxx"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/sb-docs%40mercurial-cairn-620.iam.gserviceaccount.com"
```
universe_domain = "googleapis.com"
