import os, sqlite3, json
from datetime import datetime
from app.config import SETTINGS

def connect():
    os.makedirs(os.path.dirname(SETTINGS.db_path), exist_ok=True)
    return sqlite3.connect(SETTINGS.db_path)

def init_db():
    con = connect()
    cur = con.cursor()


    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
      user_id TEXT PRIMARY KEY,
      email TEXT NOT NULL UNIQUE,
      created_at TEXT NOT NULL,
      last_login_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS otp_requests (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      email TEXT NOT NULL,
      otp_hash TEXT NOT NULL,
      expires_at TEXT NOT NULL,
      created_at TEXT NOT NULL,
      attempts_left INTEGER NOT NULL DEFAULT 5
    )
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_otp_email ON otp_requests(email)
    """)

    # TAXONOMY TREE (adjacency list)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS taxonomy_nodes (
      node_id INTEGER PRIMARY KEY AUTOINCREMENT,
      parent_id INTEGER,
      node_type TEXT NOT NULL,   -- domain/department/use_case/attack_type
      name TEXT NOT NULL,
      path TEXT NOT NULL UNIQUE,
      FOREIGN KEY(parent_id) REFERENCES taxonomy_nodes(node_id)
    )
    """)

    # prompts linked to attack_type nodes
    cur.execute("""
    CREATE TABLE IF NOT EXISTS prompts (
      prompt_id TEXT PRIMARY KEY,
      taxonomy_node_id INTEGER NOT NULL,
      domain TEXT NOT NULL,
      department TEXT NOT NULL,
      use_case TEXT NOT NULL,
      attack_type TEXT NOT NULL,
      risk_level TEXT NOT NULL,
      expected_behavior TEXT NOT NULL,
      policy_tags TEXT NOT NULL,
      prompt_text TEXT NOT NULL,
      FOREIGN KEY(taxonomy_node_id) REFERENCES taxonomy_nodes(node_id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS runs (
      run_id TEXT PRIMARY KEY,
      created_at TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS responses (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      run_id TEXT NOT NULL,
      prompt_id TEXT NOT NULL,
      model_name TEXT NOT NULL,
      response_text TEXT NOT NULL,
      latency_ms INTEGER NOT NULL,
      meta TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS results (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      run_id TEXT NOT NULL,
      prompt_id TEXT NOT NULL,
      model_name TEXT NOT NULL,
      PV REAL, HL REAL, FC REAL, SUIT REAL, FRAUD REAL, TX REAL, RA REAL, RTRI REAL,
      weights TEXT NOT NULL,
      decision_label TEXT NOT NULL,
      decision_reason TEXT NOT NULL,
      rai_transparency_ok INTEGER NOT NULL,
      rai_suitability_ok INTEGER NOT NULL,
      rai_notes TEXT NOT NULL
    )
    """)

    con.commit()
    con.close()

def upsert_taxonomy_node(parent_id, node_type, name, path) -> int:
    con = connect()
    cur = con.cursor()
    cur.execute("SELECT node_id FROM taxonomy_nodes WHERE path=?", (path,))
    row = cur.fetchone()
    if row:
        con.close()
        return row[0]

    cur.execute(
        "INSERT INTO taxonomy_nodes(parent_id, node_type, name, path) VALUES(?,?,?,?)",
        (parent_id, node_type, name, path)
    )
    node_id = cur.lastrowid
    con.commit()
    con.close()
    return node_id

def insert_prompt(p):
    con = connect()
    cur = con.cursor()
    cur.execute("""
    INSERT OR REPLACE INTO prompts(
      prompt_id, taxonomy_node_id, domain, department, use_case, attack_type, risk_level,
      expected_behavior, policy_tags, prompt_text
    ) VALUES (?,?,?,?,?,?,?,?,?,?)
    """, (
        p.prompt_id, p.taxonomy_node_id, p.domain, p.department, p.use_case, p.attack_type, p.risk_level,
        p.expected_behavior, json.dumps(p.policy_tags), p.prompt_text
    ))
    con.commit()
    con.close()

def insert_run(run_id: str):
    con = connect()
    cur = con.cursor()
    cur.execute("INSERT OR REPLACE INTO runs(run_id, created_at) VALUES(?,?)",
                (run_id, datetime.utcnow().isoformat()))
    con.commit()
    con.close()

def insert_response(run_id, prompt_id, model_name, text, latency_ms, meta):
    con = connect()
    cur = con.cursor()
    cur.execute("""
    INSERT INTO responses(run_id, prompt_id, model_name, response_text, latency_ms, meta)
    VALUES (?,?,?,?,?,?)
    """, (run_id, prompt_id, model_name, text, latency_ms, json.dumps(meta)))
    con.commit()
    con.close()

def insert_result(run_id, prompt_id, model_name, score, decision, rai):
    con = connect()
    cur = con.cursor()
    cur.execute("""
    INSERT INTO results(
      run_id, prompt_id, model_name,
      PV, HL, FC, SUIT, FRAUD, TX, RA, RTRI, weights,
      decision_label, decision_reason,
      rai_transparency_ok, rai_suitability_ok, rai_notes
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        run_id, prompt_id, model_name,
        score.PV, score.HL, score.FC, score.SUIT, score.FRAUD, score.TX, score.RA, score.RTRI, json.dumps(score.weights),
        decision.label, decision.reason,
        1 if rai.transparency_ok else 0,
        1 if rai.suitability_ok else 0,
        json.dumps(rai.audit_notes)
    ))
    con.commit()
    con.close()