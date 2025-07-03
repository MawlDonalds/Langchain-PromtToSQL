import os
from langchain_community.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.agent_toolkits import create_sql_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.callbacks import BaseCallbackHandler
from io import StringIO
import sys

# Kelas CallbackHandler untuk menangkap query SQL dari log verbose
class SQLCaptureCallback(BaseCallbackHandler):
    def __init__(self):
        self.sql_query = None
        self.output_buffer = StringIO()

    def on_tool_end(self, output, **kwargs):
        # Tangkap output dari alat SQL (biasanya query SQL yang dijalankan)
        if isinstance(output, str) and "SELECT" in output.upper():
            self.sql_query = output

    def get_sql_query(self):
        return self.sql_query

# Konfigurasi API Key Google (hardcoded)
google_api_key = "AIzaSyCg9s6LVrv5_z14QwAaGJnpYMIDU0lIjXc"  # Pastikan ini API key Anda
if not google_api_key:
    raise ValueError("GOOGLE_API_KEY belum diatur")

# Set API key sebagai variabel lingkungan
os.environ["GOOGLE_API_KEY"] = google_api_key

# Konfigurasi koneksi database PostgreSQL lokal (dengan kata sandi)
db_config = {
    "dbname": "test_db",
    "user": "postgres",
    "password": "admin123",
    "host": "localhost",
    "port": "5432"
}

# Membuat string koneksi dengan kata sandi
connection_string = f"postgresql+psycopg2://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['dbname']}"

# Inisialisasi database dengan penanganan error (tanpa include_tables untuk mendeteksi semua tabel)
try:
    db = SQLDatabase.from_uri(connection_string)
    print("Berhasil terhubung ke database")
    # Tampilkan daftar tabel yang terdeteksi untuk debugging
    tables = db.get_usable_table_names()
    print(f"Tabel yang terdeteksi: {tables}")
except Exception as e:
    print(f"Gagal terhubung ke database: {str(e)}")
    raise

# Inisialisasi model bahasa (Gemini)
try:
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)
except Exception as e:
    print(f"Gagal menginisialisasi LLM: {str(e)}")
    raise

# Ambil skema tabel secara dinamis untuk prompt
def get_dynamic_schema(db):
    schema_info = ""
    tables = db.get_usable_table_names()
    for table in tables:
        # Dapatkan informasi kolom untuk setiap tabel
        columns = db.get_table_info([table]).split('\n')
        schema_info += f"- Tabel '{table}':\n"
        for line in columns:
            if line.strip().startswith('Column') or line.strip().startswith('Name'):
                continue
            if line.strip():
                schema_info += f"  - {line.strip()}\n"
    return schema_info

# Prompt kustom dengan skema dinamis
schema = get_dynamic_schema(db)
prompt = ChatPromptTemplate.from_template(
    "Anda adalah asisten SQL yang memahami bahasa Indonesia. Ubah pertanyaan berikut menjadi query SQL berdasarkan skema database: {input}. "
    "Skema database:\n{schema}\n"
    "Kembalikan hanya jawaban dalam bahasa Indonesia tanpa query SQL."
).partial(schema=schema)

# Membuat agen SQL dengan callback untuk menangkap query
sql_callback = SQLCaptureCallback()
agent = create_sql_agent(
    llm=llm,
    db=db,
    agent_type="tool-calling",  # Gunakan tool-calling untuk kompatibilitas dengan Gemini
    verbose=True,
    callbacks=[sql_callback]
)

# Fungsi untuk menjalankan query
def run_query(query):
    try:
        # Bersihkan query SQL sebelumnya
        sql_callback.sql_query = None
        # Gunakan invoke alih-alih run untuk menghindari peringatan deprecated
        response = agent.invoke({"input": query})["output"]
        # Ambil query SQL dari callback
        sql_query = sql_callback.get_sql_query()
        return {"result": response, "sql_query": sql_query}
    except Exception as e:
        return {"result": f"Error: {str(e)}", "sql_query": None}

# Loop untuk menerima input query dari pengguna
print("\nMasukkan query dalam bahasa Indonesia (ketik 'keluar' untuk berhenti):")
while True:
    query = input("Query: ")
    if query.lower() == "keluar":
        print("Program selesai.")
        break
    print(f"\nQuery: {query}")
    result = run_query(query)
    if result["sql_query"]:
        print(f"Query SQL yang dihasilkan: {result['sql_query']}")
    print(f"Hasil: {result['result']}")