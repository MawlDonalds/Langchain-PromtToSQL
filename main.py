import os
from langchain_community.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.agent_toolkits import create_sql_agent
from dotenv import load_dotenv

load_dotenv()

google_api_key = "AIzaSyBqIwIaodwOR6gWyJM2bfFi-IMBocJ8euQ"
if not google_api_key:
    raise ValueError("GOOGLE_API_KEY belum diatur")

# Konfigurasi API Key OpenAI
os.environ["GOOGLE_API_KEY"] = google_api_key  # Ganti dengan API key Anda

# Konfigurasi koneksi database PostgreSQL lokal
db_config = {
    "dbname": "test_db",
    "user": "postgres",  # Ganti dengan username PostgreSQL Anda
    "password": "maulana18094",  # Ganti dengan password PostgreSQL Anda
    "host": "localhost",
    "port": "5432"
}

# Membuat string koneksi
connection_string = f"postgresql+psycopg2://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['dbname']}"


# Inisialisasi database
db = SQLDatabase.from_uri(connection_string)

# Inisialisasi model bahasa (LLM)
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)

# Membuat agen SQL
agent = create_sql_agent(
    llm=llm,
    db=db,
    agent_type="openai-tools",
    verbose=True
)

# Fungsi untuk menjalankan query
def run_query(query):
    try:
        response = agent.run(query)
        return response
    except Exception as e:
        return f"Error: {str(e)}"

# Contoh query
queries = [
    "tunjukan departemen apa saja yang ada",
]

# Menjalankan query dan mencetak hasil
for query in queries:
    print(f"\nQuery: {query}")
    print(f"Result: {run_query(query)}")