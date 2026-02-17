@echo off
cd /d %~dp0
call ..\env\Scripts\activate
python -m streamlit run app.py
