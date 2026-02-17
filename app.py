from streamlit_cookies_controller import CookieController
from utils import *
import streamlit as st
import time
import random

if 'bulan' not in st.session_state:
    st.session_state.bulan = ["Januari","Februari","Maret","April","Mei","Juni",
                            "Juli","Agustus","September","Oktober","November","Desember"]

male, female, bps, logo = get_images()
cookie = CookieController()

st.set_page_config(page_title="SiPENDEKAR", page_icon="images/logopendekar.png")

@st.fragment
def login_page():
    st.html("""
        <style>
        .st-key-my_blue_container {
            background-color: rgb(145, 250, 210);
        }

        .st-key-login_container {
            background-color: white;
            padding: 20px;
            border-radius: 5px;
        }
        </style>
        """)
    
    with st.container(key='my_blue_container', border=True, gap='xxsmall'):
        st.space('small')
        col_info, col_login = st.columns(2)
        with col_info:
            st.markdown("### *Selamat Datang*👋😄", text_alignment='center')
            st.markdown(
                f"""
                <div style="
                    display:flex;
                    flex-direction:column;
                    align-items:center;
                    justify-content:center;
                ">
                    <img src="data:image/png;base64,{logo}"
                        width="100"
                        style="margin-left:-30px;">
                    <h1 style="
                        margin-left:18px;
                        font-weight:bold;
                        letter-spacing:0;
                        line-height:0;
                        white-space:nowrap;
                    ">
                        <span style="color:#2563eb">Si</span><span style="color:#16a34a">PEND</span><span style="color:#f97316">EKAR</span>
                    </h1>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.markdown("<h6 style='text-align: center; color: black;'>(Sistem Penilaian dan Evaluasi Karyawan)</h6>", unsafe_allow_html=True)
            st.markdown(
                f"""
                <div style="
                    display:flex;
                    justify-content:center;
                    gap:8px;
                ">
                    <img src="data:image/png;base64,{bps}" width="30">
                    <span style="
                        margin:0;
                        font-weight:bold;
                        font-size:18;
                    ">
                        BPS Kabupaten/Kota/Provinsi
                    </span>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.space('xxsmall')
            st.info("Hubungi pihak Operator untuk mereset password atau mendaftar.")

        with col_login:
            with st.container(key="login_container", gap='xxsmall'):
                with st.form(key="login", border=False):
                    st.write("#### :material/account_circle: username")
                    uname = st.text_input("l", label_visibility='collapsed')
                    st.write("#### :material/lock: password")
                    password = st.text_input("p", type="password", label_visibility='collapsed')
                    colLogin, colInfo, colDemo = st.columns([3,4.5,3], gap='xxsmall', vertical_alignment='center')

                    if colLogin.form_submit_button("Login", type="primary"):
                        with st.spinner("Memproses login..."):
                            user = fetch_one("""
                                    SELECT
                                        u.id_user,
                                        u.password,
                                        u.penilai AS role,
                                        p.nama,
                                        p.jabatan,
                                        p.jenis_kelamin
                                    FROM users u
                                    JOIN pegawai p ON u.id_pegawai = p.id_pegawai
                                    WHERE u.username = %s AND u.password = %s
                                    """, (uname, password))

                            if user:
                                cookie.set('role', user['role'], max_age=5400)
                                cookie.set('id_user', user['id_user'], max_age=5400)
                                cookie.set('key', hash(user['password']), max_age=5400)

                                st.session_state['key'] = hash(user['password'])
                                user.pop('password', None)
                                st.session_state.update(user)
                                st.toast(f"Login Berhasil, Selamat Datang {user['nama']}")
                                time.sleep(0.5)
                                st.rerun()

                            else:
                                st.error("❌ Email atau password salah. Silakan coba lagi.")

                    colInfo.caption("Tidak punya akun? Login sebagai", text_alignment='right')
                    if colDemo.form_submit_button("Tamu", type='secondary'):
                        cookie.set('id_user', 999, max_age=10)
                        cookie.set('key', 999, max_age=10)
                        cookie.set('role', 1, max_age=10)

                        st.session_state.id_user = 999
                        st.session_state.role = 1
                        st.session_state.key = 999
                        st.session_state.nama = "Demo"
                        st.session_state.jabatan = "Pengunjung"
                        st.session_state.demo_avatar = random.randint(1, 70)
                        st.toast(f"Login Berhasil sebagai Tamu")
                        time.sleep(0.5)
                        st.rerun()

                    st.caption("Dibuat Oleh Mahasiswa Statistika Universitas Negeri Medan © 2026.", text_alignment='center')

@st.dialog("Apakah Anda yakin ingin keluar?", dismissible=False)
def logout():
    logout_area = st.empty()
    with logout_area.container():
        time.sleep(0.5)
        col1, col2 = st.columns([1.8, 9])
        if col1.button("Batal", key="reject"):
            st.switch_page("admin/dashboard.py")
        confirm_logout = col2.button("Ya, Keluar", type="primary", key='accept')

    if confirm_logout:
        logout_area.empty() 
        with st.spinner("Sedang Memproses Mohon Tunggu..."):
            for key in ['role', 'id_user', 'key']:
                if cookie.get(key):
                    cookie.remove(key)
            st.session_state.clear()
            time.sleep(0.5)
            st.switch_page(st.Page(login_page))

if not (st.session_state.get('id_user') or st.session_state.get('key')):
    st.session_state.role = cookie.get("role")
    st.session_state.id_user = cookie.get("id_user")
    st.session_state.key = cookie.get('key')
    time.sleep(2)

    if cookie.get("key") and cookie.get('id_user'):
        try:
            key = fetch_one("SELECT password FROM users WHERE id_user = %s",(cookie.get("id_user"),))['password']
        except:
            for key in ['role', 'id_user', 'key']:
                if cookie.get(key):
                    cookie.remove(key)
            st.session_state.clear()
            time.sleep(0.5)
            st.switch_page(st.Page(login_page))

        st.session_state.key = hash(key) if key is not None else None
        if st.session_state.key is not None and str(st.session_state.key) == str(cookie.get("key")):
            user = fetch_one("""
                    SELECT
                        p.nama,
                        p.jabatan,
                        p.jenis_kelamin
                    FROM users u
                    JOIN pegawai p ON u.id_pegawai = p.id_pegawai
                    WHERE p.id_pegawai = %s AND u.password = %s
                    """, (cookie.get('id_user'), key))
            
            st.session_state.update(user)

if (not st.session_state.id_user
    or not st.session_state.key
    or st.session_state.id_user != cookie.get("id_user")
    or st.session_state.key != cookie.get("key")):
    st.markdown("""
            <style>
            section[data-testid="stSidebar"] {
                display: none;
            }
            </style>
            """, unsafe_allow_html=True)
    nav = st.navigation([st.Page(login_page)])

else:
    role = st.session_state.get('role')
    jk = st.session_state.get('jenis_kelamin')

    if st.session_state.id_user == 999:
        img_sidebar = f"https://i.pravatar.cc/150?img={st.session_state.demo_avatar}"
    else :  
        img_sidebar = f"data:image/png;base64,{male if jk == 1 else female}"
    with st.sidebar:
        st.markdown(
            f"""
            <div style="text-align:center; padding:12px 0;">
                <img src="{img_sidebar}"
                    style="border-radius:50%;
                            width:80px;
                            height:80px;">
                <div style="margin-top:8px; font-weight:600;">{st.session_state.nama}_{st.session_state.demo_avatar}</div>
                <div style="font-size:12px; opacity:0.6;">{st.session_state.jabatan}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        colOut, colDetail = st.columns([2,1], gap='xxsmall')
        colOut.button("Logout", type='primary', on_click=logout, icon=":material/logout:")
        if st.session_state.id_user != 999:
            if colDetail.button('info', key='info'):
                st.session_state.id_profil = st.session_state.id_user
                st.switch_page("pages/profil.py")
        else:
            if st.button("Ganti Foto Profil", key="ganti_foto"):
                st.session_state.demo_avatar = random.randint(1, 70)
                st.rerun()

        st.divider()
        if role == 1 :
            nav = st.navigation([st.Page("admin/dashboard.py", default=True),
                    st.Page("admin/penilaian.py"),
                    st.Page("admin/karyawan.py"),
                    st.Page("pages/profil.py")],
                    position='hidden')
            
            st.page_link(st.Page("admin/dashboard.py"), icon='📊')
            st.page_link(st.Page("admin/karyawan.py"), icon="👥")
            st.page_link(st.Page("admin/penilaian.py"), icon="📋")

        else :
            nav = st.navigation([st.Page("admin/dashboard.py"),
                    st.Page("pages/profil.py")], 
                    position='hidden')
            
            st.page_link(st.Page("admin/dashboard.py"), icon='📊')

nav.run()