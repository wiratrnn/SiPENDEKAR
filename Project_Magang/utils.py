import mysql.connector
from streamlit.delta_generator import DeltaGenerator
import streamlit as st
import base64
import hashlib

def metric_card(self, title, value, icon="⭐", bg_color="#ffffff"):
    self.markdown(
        f"""
        <div style="
            background-color:{bg_color};
            padding:10px;
            border-radius:12px;
            color:white;
            height:80px;
            display:flex;
            align-items:center;
            justify-content:flex-start;
            border:3px solid black;
            margin-bottom:10px;
        ">
            <div style="font-size:30px; opacity:0.8;">
                {icon}
            </div>
            <div style="
                display:flex;
                flex-direction:column;
                align-items:flex-start;        
                align-items:center;
                width:100%;
            ">
                <div style="font-size:15px; 
                    font-weight:500; 
                    margin-top:5px;
                    width:100%;
                    white-space:nowrap;
                    overflow:hidden;
                    text-overflow:ellipsis;
                    text-align:center;
                    ">{title}</div>
                <div style="font-size:30px; font-weight:bold;">{value}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

DeltaGenerator.metric_card = metric_card

@st.cache_data
def get_images():
    with open("images/maleprofil.png", "rb") as f:
        male = base64.b64encode(f.read()).decode()
        
    with open("images/femaleprofil.png", "rb") as f:
        female = base64.b64encode(f.read()).decode()
    
    with open("images/logobps.png", "rb") as f:
        bps = base64.b64encode(f.read()).decode()

    with open("images/logopendekar.png", "rb") as f:
        logo = base64.b64encode(f.read()).decode()
    
    return male, female, bps, logo

@st.cache_data
def get_tahun():
    return fetch_all("""
            SELECT DISTINCT tahun
            FROM periode
            ORDER BY tahun;
            """)

def is_periode(id_periode):
    row = fetch_one("""
        SELECT COUNT(*) AS jumlah
        FROM nilai_aspek
        WHERE id_periode = %s
        """, (id_periode,))
    return row["jumlah"] > 0

def get_bio(id_profil):
    return fetch_one("""
            SELECT 
                p.id_pegawai,
                p.nama,
                p.jabatan,
                p.jenis_kelamin,
                u.email
            FROM pegawai p
            JOIN users u ON u.id_user = p.id_pegawai
            WHERE p.id_pegawai = %s
            """, (id_profil,))

def fn(x):
    return f"{x:.2f}".rstrip("0").rstrip(".")

def hash(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def connection():
    return mysql.connector.connect(
        host='gateway01.ap-southeast-1.prod.aws.tidbcloud.com',
        user='U9TNCA3EMhcVGNL.root',
        password='I5631lrUfemTrr5C',
        database='SIPENDEKAR',
        port=4000)

def fetch_one(query, params=None):
    with connection() as conn:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchone()

def fetch_all(query, params=None):
    with connection() as conn:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchall()

def execute_all(query, params):
    with connection() as conn:
        with conn.cursor() as cursor:
            cursor.executemany(query, params)
            conn.commit()
            
            return cursor.rowcount

def sync_total(id_pegawai, id_periode):
    with connection() as conn:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT na.nilai, a.bobot, na.id_penilai
                FROM nilai_aspek na
                JOIN aspek a ON a.id_aspek = na.id_aspek
                WHERE na.id_pegawai=%s AND na.id_periode=%s
                """, (id_pegawai, id_periode))
            rows = cursor.fetchall()

            if not rows:
                return "gagal menambah"

            total = sum(r["nilai"] * r["bobot"] for r in rows)
            jml_penilai = len({r["id_penilai"] for r in rows})
            hasil = round((total / 100) / jml_penilai, 2)

            cursor.execute("""
                INSERT INTO nilai_total (id_pegawai,id_periode,nilai)
                VALUES (%s,%s,%s)
                ON DUPLICATE KEY UPDATE nilai=VALUES(nilai)
                """, (id_pegawai, id_periode, hasil))

            conn.commit()
            return cursor.rowcount