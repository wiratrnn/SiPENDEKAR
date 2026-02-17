import time
import streamlit as st
from utils import *

def t_jaspek(judul):
    st.markdown(
            f"""
            <div style="text-align: left; margin-bottom:1rem;">
                <span style="
                    background-color: #008f58;
                    color: #f3f3f3;
                    font-weight: 700;
                    padding: 6px 14px;
                    border-radius: 8px;
                    font-size: 2.25rem;
                ">
                    {judul}
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )

@st.dialog("Verifikasi Nilai")
def verif(total, nilai):
    st.markdown(f'Nilai yang diperoleh oleh {st.session_state.target['nama']} sebesar **{total}**')

    if st.session_state.get("id_user") == 999:
        with st.container():
            st.info("Ini hanya simulasi, data perhitungan tidak akan dimasukkan ke database.")
            if st.button("Oke", key="oke_simulasi", type="primary"):
                st.session_state.pop("target", None)
                st.rerun()
    else:
        verif_area = st.empty()
        with verif_area.container():
            col1, col2 = st.columns([1.8, 9])
            if col1.button("Batal", key="reject"):
                st.rerun()
            confirm_verif = col2.button("Ya, Benar", type="primary", key='accept')

        if confirm_verif:
            verif_area.empty() 
            with st.status("Sedang Memproses...", expanded=True) as status:
                cek = execute_all("""
                        INSERT INTO nilai_aspek
                        (id_pegawai, id_penilai, id_periode, id_aspek, id_jaspek, nilai)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                        nilai = VALUES(nilai)
                        """,(nilai))
                time.sleep(1)
                if cek:
                    st.write("Berhasil Menambah nilai aspek...")
                cek2 = sync_total(st.session_state.target['id_pegawai'], st.session_state.target['id_periode'])
                time.sleep(1.5)
                if cek2:
                    st.write("Berhasil Menambah nilai total...")
                time.sleep(1.5)
                status.update(label="Selesai!", state="complete", expanded=False)
                time.sleep(1)
                st.session_state.pop("target", None)
                st.rerun()

if "target" not in st.session_state:
    st.session_state.target = None

st.title("📋 Pemberian Nilai Karyawan")
nama_pegawai = fetch_one("""
    SELECT GROUP_CONCAT(nama ORDER BY nama SEPARATOR '|') AS names
    FROM pegawai
    WHERE nama <> %s
    """,(st.session_state.nama,)
)

with st.form("Pencarian Karyawan", border=False):
    col1, col2, col3 = st.columns(3)
    nama = col1.selectbox("Nama Karyawan", nama_pegawai['names'].split("|"), index=None)
    bulan = col2.selectbox("Periode Penilaian", range(1, 13),
                            format_func=lambda x: st.session_state.bulan[x-1])
    tahun = col3.selectbox("Tahun Penilaian", [row["tahun"] for row in get_tahun()])

    if st.form_submit_button("🔍 Cari", type="primary"):
        st.session_state.target = fetch_one("""
                                        SELECT
                                            p.id_pegawai,
                                            p.nama,
                                            (   SELECT id_periode
                                                FROM periode
                                                WHERE tahun = %s AND bulan = %s
                                            ) AS id_periode
                                        FROM pegawai p
                                        WHERE p.nama = %s
                                        """, (tahun, bulan, nama))
        
        if st.session_state.target:
            st.toast(f"berhasil {st.session_state.target['nama']}")
        else :
            st.error("Data karyawan tidak ditemukan")

if st.session_state.target:
    aspek = fetch_all("SELECT * FROM aspek")
    nama_aspek = [n['nama_aspek'] for n in aspek]
    detail_aspek = [n['detail_aspek'] for n in aspek]
    bobot = [n['bobot'] for n in aspek]

    with st.form("form_penilaian", clear_on_submit=False):
        st.title("Form Penilaian", text_alignment='center')

        t_jaspek('Disiplin')
        ketepatan = st.number_input(f"**{nama_aspek[0]} ({fn(bobot[0])}%)**", value=None, min_value=0, max_value=100, step=1, key=f"{nama_aspek[0]}", placeholder=detail_aspek[0])
        kerapihan = st.number_input(f"**{nama_aspek[1]} ({fn(bobot[1])}%)**", value=None, min_value=0, max_value=100, step=1, key=f"{nama_aspek[1]}", placeholder=detail_aspek[1])
        kepatuhan = st.number_input(f"**{nama_aspek[2]} ({fn(bobot[2])}%)**", value=None, min_value=0, max_value=100, step=1, key=f"{nama_aspek[2]}", placeholder=detail_aspek[2])
        st.divider()

        t_jaspek("Sikap Kerja")
        inisiatif   = st.number_input(f"**{nama_aspek[3]} ({fn(bobot[3])}%)**", value=None, min_value=0, max_value=100, step=1, key=f"{nama_aspek[3]}", placeholder=detail_aspek[3])
        kolaboratif = st.number_input(f"**{nama_aspek[4]} ({fn(bobot[4])}%)**", value=None, min_value=0, max_value=100, step=1, key=f"{nama_aspek[4]}", placeholder=detail_aspek[4])
        st.divider()

        t_jaspek("Hasil Kerja")
        kualitas  = st.number_input(f"**{nama_aspek[5]} ({fn(bobot[5])}%)**", value=None, min_value=0, max_value=100, step=1, key=f"{nama_aspek[5]}", placeholder=detail_aspek[5])
        kuantitas = st.number_input(f"**{nama_aspek[6]} ({fn(bobot[6])}%)**", value=None, min_value=0, max_value=100, step=1, key=f"{nama_aspek[6]}", placeholder=detail_aspek[6])
        akuntabil = st.number_input(f"**{nama_aspek[7]} ({fn(bobot[7])}%)**", value=None, min_value=0, max_value=100, step=1, key=f"{nama_aspek[7]}", placeholder=detail_aspek[7])

        if st.form_submit_button("✅ hitung", width='stretch', type="primary"):
            nilai = [ketepatan or 0, kerapihan or 0, kepatuhan or 0, inisiatif or 0, 
                     kolaboratif or 0, kualitas or 0, kuantitas or 0, akuntabil or 0]
                      
            total = sum(n * b for n, b in zip(nilai, bobot)) / 100

            id_aspek = [n['id_aspek'] for n in aspek]
            id_jaspek = [n['id_jaspek'] for n in aspek]
            params = [( st.session_state.target['id_pegawai'],
                        st.session_state.id_user,
                        st.session_state.target['id_periode'],
                        aspek, jaspek, n)
                        for aspek, jaspek, n in zip(id_aspek, id_jaspek, nilai)
                        if n != 0
                        ]

            verif(fn(total), params)
