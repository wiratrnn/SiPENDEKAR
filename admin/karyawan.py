import streamlit as st
from utils import fetch_all

st.session_state.pop("target", None)
st.title("👥 Daftar Karyawan")

data = fetch_all(
    """
    SELECT 
        p.id_pegawai,
        p.nama,
        p.jabatan,
        p.jenis_kelamin,
        u.email
    FROM pegawai p
    JOIN users u ON u.id_user = p.id_pegawai;
    """
)

for row in data:
    with st.container(border=True):
        col_1, col_2 = st.columns([8, 1], vertical_alignment="center")
        with col_1:
            colNama, colEmail = st.columns(2, gap='xxsmall')
            colNama.markdown(f"**Nama**: {row['nama']}")
            colNama.write(f"**Jabatan** : {row['jabatan']}")
            colEmail.markdown(f"**Email:** {row['email']}")

        with col_2:
            if st.button("detail", key=f"info_{row['id_pegawai']}"):
                st.session_state.id_profil = row["id_pegawai"]
                st.switch_page("pages/profil.py")