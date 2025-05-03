# agents/data_retrieval.py
import duckdb
from pgvector.psycopg import connect

class DataRetrievalAgent:
    def __init__(self, duckdb_path=":memory:", pg_conn_str=None):
        self.duck = duckdb.connect(duckdb_path)
        self.pg = connect(pg_conn_str) if pg_conn_str else None

    def fetch_historical_failures(self, test_name: str):
        query = f"SELECT * FROM test_runs WHERE test_name = '{test_name}' AND status='failed';"
        return self.duck.execute(query).fetchdf()

    def fetch_similar_context(self, text: str, top_k=5):
        cur = self.pg.cursor()
        cur.execute(
            "SELECT snippet, embedding <-> embed($1) AS dist FROM code_chunks ORDER BY dist LIMIT %s;",
            (text, top_k)
        )
        return cur.fetchall()
