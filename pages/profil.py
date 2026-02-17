import streamlit as st
import pandas as pd
import plotly.express as px
from utils import *

biodata = get_bio(st.session_state.id_profil)

@st.cache_data(ttl=300)
def get_detail(tahun):
    return fetch_all("""
        SELECT 
            na.*,
            a.nama_aspek,
            j.judul_aspek,
            p.bulan,
            p.tahun,
            nt.nilai AS total
        FROM nilai_aspek na
        JOIN nilai_total nt 
            ON nt.id_pegawai = na.id_pegawai
            AND nt.id_periode = na.id_periode
        JOIN aspek a
            ON a.id_aspek = na.id_aspek
        JOIN jaspek j
            ON j.id_jaspek = na.id_jaspek
        JOIN periode p
            ON p.id_periode = na.id_periode
        WHERE na.id_pegawai = %s
        AND p.tahun = %s
        ORDER BY p.bulan
    """, (biodata['id_pegawai'], tahun))

@st.cache_data(ttl=300)
def get_jaspek(tahun):
    return fetch_all("""
        SELECT 
            na.id_periode,
            p.bulan,
            p.tahun,
            na.id_jaspek,
            j.judul_aspek,
            ROUND(
                SUM(na.nilai * a.bobot) / 100
                /
                NULLIF(
                    (
                        SELECT COUNT(DISTINCT id_penilai)
                        FROM nilai_aspek
                        WHERE id_pegawai = %s
                        AND id_periode = na.id_periode
                    ),
                0)
            , 2) AS total
        FROM nilai_aspek na
        JOIN aspek a ON a.id_aspek = na.id_aspek
        JOIN periode p ON p.id_periode = na.id_periode
        JOIN jaspek j ON j.id_jaspek = na.id_jaspek
        WHERE na.id_pegawai = %s 
          AND p.tahun = %s
        GROUP BY 
            na.id_periode, p.bulan, p.tahun,
            na.id_jaspek, j.judul_aspek
        ORDER BY p.tahun, p.bulan
        """, (biodata['id_pegawai'],biodata['id_pegawai'], tahun))

def hitung_delta(df, periode):
    now = df[df["id_periode"] == periode]
    prev = df[df["id_periode"] == periode - 1]

    if not now.empty and not prev.empty:
        return now.iloc[0]["total"] - prev.iloc[0]["total"]
    return None

def get_nilai(df, periode):
    now = df[df["id_periode"] == periode]
    if not now.empty:
        return now.iloc[0]["total"]
    return 0

@st.dialog("Informasi Halaman Profil", width="medium")
def Penjelasan():
    st.info("""
    :material/info_i: Tips:
    Gunakan filter bulan dan tahun untuk melihat perubahan performa secara historis.
    """)

    st.subheader("Ringkasan Nilai Total")
    st.markdown("""
    Nilai Total menampilkan akumulasi performa karyawan pada periode yang dipilih. 
    Angka di bawahnya menunjukkan perubahan dibanding periode sebelumnya.
    - Panah hijau :green-badge[:material/arrow_upward:] berarti peningkatan.
    - Panah merah :red-badge[:material/arrow_downward:] berarti penurunan.
    """)

    st.divider()

    st.subheader("Grafik Disiplin, Hasil Kerja, dan Sikap Kerja")
    st.write("""
    Setiap kartu aspek menampilkan, sama seperti nilai total, 
    Angka di bawahnya menunjukkanperubahan dibanding periode sebelumnya.
    - Skala nilai sesuai bobot maksimal (misalnya Disiplin 30% maka [0–30]).
    - Grafik garis kecil (sparkline) menunjukkan tren nilai dari Januari - Desember.
    """)

    st.divider()

    st.subheader("Performa Pegawai per Aspek Utama")
    st.write("""
    Grafik ini menampilkan kontribusi masing-masing aspek utama terhadap nilai total.
    Digunakan untuk melihat aspek mana yang paling kuat dan mana yang perlu ditingkatkan.
    """)

    st.divider()

    st.subheader("Performa Pegawai per Sub-Aspek")
    st.markdown("""
    Grafik ini memberikan detail penilaian pada level sub-aspek.
    Berguna untuk analisis lebih mendalam terhadap indikator spesifik dalam setiap aspek utama.
    - Radar biru **:blue-badge[:material/radar:]** berarti performa periode sebelumnya.
    - Radar orange **:orange-badge[:material/radar:]** berarti performa pada periode yang dipilih.
    """)

    st.divider()

    st.subheader("Tabel Rekap Penilaian")
    st.write("""
    Tabel ini menyajikan rekap nilai setiap sub-aspek dan totalnya untuk setiap periode.
    - Nilai dengan :yellow-badge[highlight] warna kuning adalah nilai sub-aspek tertinggi pada periode tersebut.
    """)


col1, col2, col3 = st.columns([1, 3, 2], gap='xxsmall')
with col1:
    st.space()
    if biodata['jenis_kelamin'] == 1:
        st.image("images/maleprofil.png", width=90)
    else :
        st.image("images/femaleprofil.png", width=90)

with col2:
    st.subheader(biodata['nama'])
    st.caption(f"• {biodata['jabatan']} •")
    st.caption(f"{biodata['email']}")

colBulan, colTahun, colPenjelasan = st.columns([2,2,1], vertical_alignment="bottom")
Y = colTahun.selectbox("tahun periode", options=[row["tahun"] for row in get_tahun()], index=1)
M = colBulan.selectbox("Periode Penilaian", range(1, 13), index=11,
                        format_func=lambda x: st.session_state.bulan[x-1])
if colPenjelasan.button("🔎 Penjelasan"):
    Penjelasan()

periode = fetch_one("""
            SELECT id_periode
            FROM periode
            WHERE tahun=%s AND bulan=%s
            """, (Y, M))['id_periode']

if not is_periode(periode):
    st.warning(f"Belum ada data penilaian untuk periode {st.session_state.bulan[M-1]} {Y}.")
    st.stop()


jaspek_df = pd.DataFrame(get_jaspek(Y))
data_df = pd.DataFrame(get_detail(Y))

total_per_periode    = data_df[["id_periode", "total"]].drop_duplicates().sort_values("id_periode")
disiplin_per_periode = jaspek_df[jaspek_df["id_jaspek"] == 1][["id_periode", "total"]]
sikap_per_periode    = jaspek_df[jaspek_df["id_jaspek"] == 2][["id_periode", "total"]]
kerja_per_periode    = jaspek_df[jaspek_df["id_jaspek"] == 3][["id_periode", "total"]]

delta_total    = hitung_delta(total_per_periode, periode)
delta_disiplin = hitung_delta(disiplin_per_periode, periode)
delta_sikap    = hitung_delta(sikap_per_periode, periode)
delta_kerja    = hitung_delta(kerja_per_periode, periode)

col3.metric(f"Nilai Total periode {st.session_state.bulan[M-1]} {Y}", 
          get_nilai(total_per_periode, periode), 
          delta=delta_total, 
          border=True)

c1, c2, c3 = st.columns(3, gap='xxsmall')
c1.metric("Disiplin [0 - 30]",
    get_nilai(disiplin_per_periode, periode),
    delta_disiplin,
    chart_data=disiplin_per_periode['total'],
    chart_type='line',
    border=True)
   
c2.metric("Hasil Kerja [0 - 40]",
    get_nilai(kerja_per_periode, periode),
    delta_kerja,
    chart_data=kerja_per_periode['total'],
    chart_type='line',
    border=True)

c3.metric("Sikap Kerja [0 - 30]",
    get_nilai(sikap_per_periode, periode),
    delta_sikap,
    chart_data=sikap_per_periode['total'],
    chart_type='line',
    border=True)

jaspek_df["periode"] = jaspek_df["bulan"].astype(str).str.zfill(2) + "/" + jaspek_df["tahun"].astype(str)
jaspek_df["total"] = pd.to_numeric(jaspek_df["total"], errors="coerce")

colBar, colRadar = st.columns([5,5], border=True, gap='xxsmall')
colBar.header("Performa Pegawai per Aspek Utama")
colBar.bar_chart(jaspek_df, x="periode", y="total", color="judul_aspek", 
                horizontal=True, y_label='', width=300)

urutan = ["Kepatuhan", "Ketepatan", "Inisiatif",
          "Kolaboratif","Akuntabilitas","Kuantitas",
           "Kualitas","Kerapihan"]

map_periode = (
    data_df[["id_periode", "bulan", "tahun"]]
    .drop_duplicates()
    .set_index("id_periode")
)

radar_fix = (
    data_df[data_df["id_periode"].isin([periode-1, periode])]
    .groupby(["id_periode", "nama_aspek"], as_index=False)["nilai"]
    .mean()
    .pivot(index="nama_aspek", columns="id_periode", values="nilai")
    .reindex(urutan)
    .fillna(0)
    .infer_objects(copy=False)
    .reset_index()
    .melt(id_vars="nama_aspek", var_name="periode", value_name="nilai")
)

radar_fix["periode"] = radar_fix["periode"].apply(
    lambda x: f"{map_periode.loc[x, 'bulan']}/{map_periode.loc[x, 'tahun']}"
)

fig = px.line_polar(
    radar_fix,
    r="nilai",
    theta="nama_aspek",
    color="periode",
    line_close=True,
    color_discrete_sequence=["#3366CC", "#FF9900"]
)

fig.update_traces(fill="toself", mode="lines+markers")

fig.update_layout(
    polar=dict(
        domain=dict(x=[0.3, 1], y=[0.3, 0.8]),
        angularaxis=dict(categoryorder="array", categoryarray=urutan)
    ),
    margin=dict(t=0, b=0, l=0, r=0)
)

colRadar.header("Performa Pegawai per Sub-Aspek")
colRadar.plotly_chart(fig, height=300)






# tabel
data_df["periode"] = data_df["bulan"].astype(str).str.zfill(2) + "/" + data_df["tahun"].astype(str)

tabel = (
    data_df[["periode"]].drop_duplicates().assign(key=1)
    .merge(
        data_df[["judul_aspek", "nama_aspek"]].drop_duplicates().assign(key=1),
        on="key"
    )
    .drop("key", axis=1)
    .merge(
        data_df
        .groupby(["periode", "judul_aspek", "nama_aspek"], as_index=False)["nilai"]
        .mean(),
        how="left"
    )
    .pivot(
        index="periode",
        columns=["judul_aspek", "nama_aspek"],
        values="nilai"
    )
    .join(
        data_df
        .groupby("periode")["total"]
        .first()
        .rename(("Total", "Total"))
    )
    .sort_index(axis=1)
    .reset_index()
    .fillna(0)
    .infer_objects(copy=False)
)

st.header("Tabel Rekap Penilaian")
num_cols = tabel.select_dtypes(include="number").columns
st.dataframe(tabel.style.highlight_max(axis=1,subset= num_cols)
                        .format(fn, subset=num_cols),
            width='stretch', hide_index=True)