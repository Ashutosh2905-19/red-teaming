import os, sqlite3, hashlib, secrets
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText

from app.config import SETTINGS

from dotenv import load_dotenv
load_dotenv()

def _connect():
    os.makedirs(os.path.dirname(SETTINGS.db_path), exist_ok=True)
    return sqlite3.connect(SETTINGS.db_path)

def _now_utc():
    return datetime.utcnow()

def _hash_otp(email: str, otp: str) -> str:
    # email included so OTP hash is user-specific
    return hashlib.sha256(f"{email.lower()}::{otp}".encode("utf-8")).hexdigest()

def _smtp_send(to_email: str, subject: str, body: str):
    host = os.getenv("SMTP_HOST", "")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "")
    password = os.getenv("SMTP_PASS", "")
    sender = os.getenv("SMTP_FROM", user)

    if not (host and user and password and sender):
        raise RuntimeError("SMTP env vars missing. Set SMTP_HOST/SMTP_USER/SMTP_PASS/SMTP_FROM in .env")

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to_email

    with smtplib.SMTP(host, port) as s:
        s.starttls()
        s.login(user, password)
        s.sendmail(sender, [to_email], msg.as_string())

def send_otp(email: str) -> None:
    email = (email or "").strip().lower()
    if "@" not in email:
        raise ValueError("Invalid email")

    expiry_min = int(os.getenv("OTP_EXPIRY_MINUTES", "10"))
    otp = f"{secrets.randbelow(1000000):06d}"  # 6 digits
    otp_hash = _hash_otp(email, otp)

    created_at = _now_utc()
    expires_at = created_at + timedelta(minutes=expiry_min)

    con = _connect()
    cur = con.cursor()

    # Optional: cooldown (avoid spam)
    cooldown_s = int(os.getenv("OTP_COOLDOWN_SECONDS", "60"))
    cur.execute("""
      SELECT created_at FROM otp_requests
      WHERE email=?
      ORDER BY id DESC LIMIT 1
    """, (email,))
    row = cur.fetchone()
    if row:
        last = datetime.fromisoformat(row[0])
        if (created_at - last).total_seconds() < cooldown_s:
            con.close()
            raise RuntimeError(f"Please wait {cooldown_s} seconds before requesting another OTP.")

    cur.execute("""
      INSERT INTO otp_requests(email, otp_hash, expires_at, created_at, attempts_left)
      VALUES (?,?,?,?,?)
    """, (email, otp_hash, expires_at.isoformat(), created_at.isoformat(), 5))

    con.commit()
    con.close()

    # Send email
    subject = "Your Login OTP"
    body = f"Your OTP is: {otp}\n\nIt expires in {expiry_min} minutes."
    _smtp_send(email, subject, body)

def verify_otp(email: str, otp: str) -> bool:
    email = (email or "").strip().lower()
    otp = (otp or "").strip()

    if not otp.isdigit() or len(otp) != 6:
        return False

    con = _connect()
    cur = con.cursor()

    cur.execute("""
      SELECT id, otp_hash, expires_at, attempts_left
      FROM otp_requests
      WHERE email=?
      ORDER BY id DESC LIMIT 1
    """, (email,))
    row = cur.fetchone()

    if not row:
        con.close()
        return False

    req_id, otp_hash, expires_at_s, attempts_left = row
    expires_at = datetime.fromisoformat(expires_at_s)

    if _now_utc() > expires_at or attempts_left <= 0:
        con.close()
        return False

    if _hash_otp(email, otp) != otp_hash:
        # decrease attempts
        cur.execute("UPDATE otp_requests SET attempts_left = attempts_left - 1 WHERE id=?", (req_id,))
        con.commit()
        con.close()
        return False

    con.close()
    return True

def get_or_create_user(email: str) -> str:
    email = (email or "").strip().lower()

    # stable user_id derived from email (same user across sessions)
    user_id = hashlib.sha256(email.encode("utf-8")).hexdigest()[:16]

    con = _connect()
    cur = con.cursor()

    cur.execute("SELECT user_id FROM users WHERE email=?", (email,))
    row = cur.fetchone()
    now = _now_utc().isoformat()

    if row:
        cur.execute("UPDATE users SET last_login_at=? WHERE email=?", (now, email))
        con.commit()
        con.close()
        return row[0]

    cur.execute("""
      INSERT INTO users(user_id, email, created_at, last_login_at)
      VALUES (?,?,?,?)
    """, (user_id, email, now, now))

    con.commit()
    con.close()
    return user_id