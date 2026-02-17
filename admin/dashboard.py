import streamlit as st
import pandas as pd
import plotly.express as px
from utils import *

warna = px.colors.qualitative.G10

st.session_state.pop("target", None)

@st.cache_data(ttl=300)
def get_bar_data(periode):
    return fetch_all("""
        SELECT nilai
        FROM nilai_total
        WHERE id_periode = %s
        """, (periode,))

@st.cache_data(ttl=300)
def get_top5_data(periode):
    return fetch_all("""
        SELECT *
        FROM (
            SELECT 
                p.nama,
                ROUND(
                    SUM(CASE WHEN na.id_jaspek = 1 
                            THEN na.nilai * a.bobot END)
                    / NULLIF(
                        SUM(CASE WHEN na.id_jaspek = 1 
                                THEN a.bobot END),
                    0)
                , 2) AS Disiplin,

                ROUND(
                    SUM(CASE WHEN na.id_jaspek = 2 
                            THEN na.nilai * a.bobot END)
                    /
                    NULLIF(
                        SUM(CASE WHEN na.id_jaspek = 2 
                                THEN a.bobot END),
                    0)
                , 2) AS Sikap_Kerja,

                ROUND(
                    SUM(CASE WHEN na.id_jaspek = 3 
                            THEN na.nilai * a.bobot END)
                    /
                    NULLIF(
                        SUM(CASE WHEN na.id_jaspek = 3 
                                THEN a.bobot END),
                    0)
                , 2) AS Hasil_Kerja,

                ROUND(n.nilai,2) AS Total

            FROM pegawai p

            LEFT JOIN nilai_total n 
                ON p.id_pegawai = n.id_pegawai 
                AND n.id_periode = %s

            LEFT JOIN nilai_aspek na 
                ON p.id_pegawai = na.id_pegawai 
                AND na.id_periode = %s

            LEFT JOIN aspek a 
                ON a.id_aspek = na.id_aspek

            GROUP BY p.id_pegawai, p.nama, n.nilai
        ) AS hasil
    """, (periode, periode))

@st.cache_data(ttl=300)
def get_line_data(tahun):
    return fetch_all("""
        SELECT 
            p.id_periode, p.tahun, p.bulan,
            ROUND(AVG(CASE WHEN t.id_jaspek = 1 THEN t.skor_pegawai END), 2) AS disiplin,
            ROUND(AVG(CASE WHEN t.id_jaspek = 2 THEN t.skor_pegawai END), 2) AS sikap_kerja,
            ROUND(AVG(CASE WHEN t.id_jaspek = 3 THEN t.skor_pegawai END), 2) AS hasil_kerja,
            (SELECT ROUND(AVG(nt.nilai), 2) 
            FROM nilai_total nt 
            WHERE nt.id_periode = p.id_periode) AS total

        FROM (
            SELECT n.id_periode, n.id_pegawai, n.id_jaspek,
                SUM(n.nilai * a.bobot) / SUM(a.bobot) AS skor_pegawai
            FROM nilai_aspek n
            JOIN aspek a USING (id_aspek)
            GROUP BY n.id_periode, n.id_pegawai, n.id_jaspek
        ) t
        JOIN periode p USING (id_periode)
        WHERE p.tahun = %s
        GROUP BY p.id_periode, p.tahun, p.bulan
        ORDER BY p.bulan ASC
        """,(tahun,))

@st.cache_data(ttl=300)
def get_hbar_data(periode):
    return fetch_all("""
        SELECT a.nama_aspek, AVG(na.nilai) AS rata
        FROM nilai_aspek na
        JOIN aspek a ON a.id_aspek = na.id_aspek
        WHERE na.id_periode = %s
        GROUP BY a.id_aspek, a.nama_aspek
        ORDER BY rata
        """, (periode,))

@st.cache_data(ttl=300)
def metric_data(id_periode):
    return fetch_one("""
        SELECT 
            AVG(nt.nilai) AS avg_nilai, 
            MAX(nt.nilai) AS max_nilai,
            MIN(nt.nilai) AS min_nilai,
            (
                SELECT COUNT(DISTINCT na.id_penilai)
                FROM nilai_aspek na
                WHERE na.id_periode = nt.id_periode
            ) AS jumlah_penilai
        FROM nilai_total nt
        WHERE nt.id_periode = %s
        """, (id_periode,))

colTitle, colAktif = st.columns([6.7,3.5], gap='small')
st.divider()
colTitle.title("📊 Dashboard")

jlh_pegawai = fetch_one("SELECT COUNT(*) AS jumlah FROM pegawai WHERE status = 1")['jumlah']
colAktif.metric_card("Karyawan Aktif Saat Ini", fn(jlh_pegawai)+" Orang", "👥", "#008f58")

colBulan, colTahun = st.columns(2)
Y = colTahun.selectbox("tahun periode", options=[row["tahun"] for row in get_tahun()], index=1)
M = colBulan.selectbox("Periode Penilaian", range(1, 13), index=11,
                        format_func=lambda x: st.session_state.bulan[x-1])

periode_row = fetch_one("""
            SELECT id_periode
            FROM periode
            WHERE tahun=%s AND bulan=%s
            """, (Y, M))['id_periode']

if not is_periode(periode_row):
    st.warning(f"Belum ada data penilaian untuk periode {st.session_state.bulan[M-1]} {Y}.")
    st.stop()

stats = metric_data(periode_row)
col1, col2, col3, col4 = st.columns([3,2.4,2.4,2.4])

col1.metric_card("Jumlah Penilai", fn(stats['jumlah_penilai'])+" Orang", "⚖️", "#3366CC")
col2.metric_card("Rata-rata Nilai", fn(stats['avg_nilai']), "⭐", "#109618")
col3.metric_card("Nilai Tertinggi", fn(stats['max_nilai']), "🏆", "#FF9900")
col4.metric_card("Nilai Terendah", fn(stats['min_nilai']), "🔻", "#DC3912")
st.space('xxsmall')
colBar, colTop = st.columns([6.25,3.75], border=True)

@st.fragment
def bar_chart(periode):
    bar_df = get_bar_data(periode)
    
    BINS = [-float("inf"), 40, 50, 60, 70, 80, 90, 100]
    LABELS = ["< 40", "41-50", "51-60", "61-70", "71-80", "81-90", "91-100"]

    df = pd.DataFrame(bar_df)
    rekap_df = (
        pd.cut(df["nilai"], bins=BINS, labels=LABELS, include_lowest=True)
        .value_counts(sort=False)
        .rename_axis("range")
        .reset_index(name="jumlah")
    )

    fig = px.bar(
        rekap_df,
        x="range",
        y="jumlah",
        color='range',
        color_discrete_sequence=warna
    )

    fig.update_traces(offsetgroup=0)
    fig.update_layout(
        margin=dict(t=0, b=0),
        barmode='overlay',
        xaxis_title=f'Kumulatif Nilai per {st.session_state.bulan[M-1]} {Y}',
        yaxis_title='jumlah karyawan',
        showlegend=False
    )

    colBar.subheader("Distribusi Nilai Karyawan")
    colBar.plotly_chart(fig, height=250)
    colBar.markdown("<hr style='margin:5px 0;'>", unsafe_allow_html=True)

bar_chart(periode_row)

@st.fragment
def TOP(periode):
    df2 = get_top5_data(periode)
    colTopsis = st.container()

    medals = [
        ("🥇", "#D4AF37"),
        ("🥈", "#C0C0C0"),
        ("🥉", "#CD7F32"),
        ("🏅", "#00CC96"),
        ("🏅", "#00CC96"),
    ]

    colTopsis.markdown(f"<h3 style='margin-bottom:0'> Karyawan Terbaik Periode {st.session_state.bulan[M-1]} {Y}</h3>", unsafe_allow_html=True)
    filter = colTopsis.selectbox("Berdasarkan" , ["Total", "Disiplin", "Sikap_Kerja", "Hasil_Kerja"])
    with colTopsis.container(height=450, border=False):
        df_sorted = sorted(df2,
                        key=lambda x: (x[filter] if x[filter] is not None else -1),
                        reverse=True)
        
        for i, data in enumerate(df_sorted[:5]):
            icon, color = medals[i]
            nama = data['nama'].split(',')[0].strip()
            metric_card(st, nama, data[filter], f"{icon}", color)

        if st.session_state.role == 1:
            for i, data in enumerate(df_sorted[5:], start=6):
                nama = data['nama'].split(',')[0].strip()
                metric_card(st, nama, data[filter], icon=f"•{i}", bg_color="#8b8b8b")

with colTop:
    TOP(periode_row)

@st.fragment
def line(tahun):
    line_df = get_line_data(tahun)
    df3 = pd.DataFrame(line_df).set_index('id_periode')

    df3 = df3.apply(pd.to_numeric, errors="coerce")
    df3["periode"] = df3["tahun"].astype(str) + "-" + df3["bulan"].astype(str).str.zfill(2)

    fig1 = px.line(df3, 
                x='periode', 
                y = 'total',
                markers=True,
                color_discrete_sequence=["#109618"])
    fig1.update_xaxes(
        dtick="M1",
        tickformat="%b",
        title=""
    )
    fig1.update_yaxes(title="Nilai",
                      nticks=5)
    fig1.update_layout(
        margin=dict(t=10, b=0, r=5),
        showlegend=False
    )
    colBar.subheader(f"Tren Kinerja Karyawan per Total Aspek tahun {tahun}")
    colBar.plotly_chart(fig1, height=250)

    fig2 = px.line(df3, 
                x='periode', 
                y = ["disiplin","sikap_kerja","hasil_kerja"],
                markers=True,
                labels={"value": "Nilai (%)", "variable": "Aspek"},
                color_discrete_sequence=warna)
    fig2.update_xaxes(
        dtick="M1",
        tickformat="%b %Y",
        title=""
    )
    fig2.update_layout(
        margin=dict(t=50),
        showlegend=True,
        title=dict(
            text=f"Tren Kinerja Karyawan per Aspek Utama tahun {tahun}",
            font=dict(size=26)
        ),
    )

    with st.container(border=True):
        st.plotly_chart(fig2, height=350)

line(Y)

colDetail, colHbar, = st.columns([3.9,6.1], border=True)
@st.fragment
def hbar(periode):
    rows = get_hbar_data(periode)
    
    nama_aspek = [r["nama_aspek"] for r in rows]
    nilai = [float(r["rata"]) for r in rows]

    colHbar.markdown('#### **Performa Karyawan per Sub-Aspek**')
    fig = px.bar(
        x=nilai,
        y=nama_aspek,
        orientation="h",
        color=nama_aspek,
        color_discrete_sequence=warna,
        text=nama_aspek
    )

    fig.update_traces(offsetgroup=0,
                      width=1,
                      textposition="inside")
    fig.update_yaxes(visible=False)
    fig.update_layout(
        margin=dict(t=10, l=0, r=0, b=3),
        barmode='overlay',
        xaxis_title="Rata-rata Nilai",
        yaxis_title="",
        showlegend=False
    )
    fig.update_xaxes(range=[35, 65])
    colHbar.plotly_chart(fig, height=300)

hbar(periode_row)

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
                    font-size: 18px;
                ">
                    {judul}
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )
    
colDetail.header("Detail Penilaian Karyawan")

with colDetail.expander("Disiplin [30%]"):
    aspek = fetch_all("SELECT * FROM aspek WHERE id_jaspek = 1")
    col1, col2 = st.columns([5, 2])

    for disiplin in aspek:
        with st.container():
            col1, col2 = st.columns([5, 2])

            with col1:
                t_jaspek(disiplin['nama_aspek'])

            with col2:
                st.markdown(
                    f"""
                    <div style="
                        text-align:center;
                        padding:2px;
                        border-radius:8px;
                        font-weight:600;
                        border:1px solid #ddd;">
                        {fn(disiplin['bobot'])}%
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            st.caption(disiplin["detail_aspek"])

with colDetail.expander("Sikap Kerja [30%]"):
    aspek = fetch_all("SELECT * FROM aspek WHERE id_jaspek = 2")
    col1, col2 = st.columns([5, 2])

    for disiplin in aspek:
        with st.container():
            col1, col2 = st.columns([5, 2])

            with col1:
                t_jaspek(disiplin['nama_aspek'])

            with col2:
                st.markdown(
                    f"""
                    <div style="
                        text-align:center;
                        padding:2px;
                        border-radius:8px;
                        font-weight:600;
                        border:1px solid #ddd;">
                        {fn(disiplin['bobot'])}%
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            st.caption(disiplin["detail_aspek"])

with colDetail.expander("Hasil Kerja [40%]"):
    aspek = fetch_all("SELECT * FROM aspek WHERE id_jaspek = 3")
    col1, col2 = st.columns([5, 2])

    for disiplin in aspek:
        with st.container():
            col1, col2 = st.columns([5, 2])

            with col1:
                t_jaspek(disiplin['nama_aspek'])

            with col2:
                st.markdown(
                    f"""
                    <div style="
                        text-align:center;
                        padding:2px;
                        border-radius:8px;
                        font-weight:600;
                        border:1px solid #ddd;">
                        {fn(disiplin['bobot'])}%
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            st.caption(disiplin["detail_aspek"])

