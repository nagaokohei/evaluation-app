import streamlit as st
import sqlite3
import pandas as pd
import datetime

# --- データベース関連の関数 ---
def init_db():
    # データベースに接続（ファイルがなければ自動生成される）
    conn = sqlite3.connect('evaluation.db')
    c = conn.cursor()
    # テーブルを作る（IF NOT EXISTS で「無ければ作る」）
    c.execute('''
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            receiver TEXT,
            message TEXT,
            timestamp DATETIME
        )
    ''')
    conn.commit()
    conn.close()

def add_data(sender, receiver, message):
    conn = sqlite3.connect('evaluation.db')
    c = conn.cursor()
    # データを挿入するSQL
    c.execute('INSERT INTO evaluations (sender, receiver, message, timestamp) VALUES (?, ?, ?, ?)',
              (sender, receiver, message, datetime.datetime.now()))
    conn.commit()
    conn.close()

def view_data():
    conn = sqlite3.connect('evaluation.db')
    # Pandasを使うと一発で表形式にできるので便利
    df = pd.read_sql('SELECT * FROM evaluations', conn)
    conn.close()
    return df

# --- アプリのメイン処理 ---
st.title('ほめ合いアプリ（DB付き）')

# 最初にDBがあるか確認（無ければ作る）
init_db()

# 入力フォーム
st.subheader('メッセージを送る')
sender = st.text_input('あなたの名前')
receiver = st.text_input('相手の名前')
message = st.text_area('メッセージ')

if st.button('送信'):
    if sender and receiver and message:
        add_data(sender, receiver, message)
        st.success('保存しました！')
    else:
        st.error('全ての項目を入力してください')

# 保存されたデータの表示
st.subheader('過去のメッセージ')
df = view_data()
st.dataframe(df)
