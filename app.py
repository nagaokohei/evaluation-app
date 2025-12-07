import streamlit as st
import datetime

# 1. タイトルを表示（print文のようなもの）
st.write('# アプリ')
st.write('## ヘッダー')
# 2. 画面入力エリアを作る（read文のようなもの）

sender = st.selectbox('あなたの名前', ['佐藤', '田中', '鈴木'])
receiver = st.selectbox('感謝を伝える相手', ['佐藤', '田中', '鈴木'])
message = st.text_area('メッセージを入力', '忙しい時に手伝ってくれてありがとう！')

# 3. ボタンが押された時の処理（If文）
if st.button('送信する'):
    # ここに保存処理を書きます
    timestamp = datetime.datetime.now()
    
    # 画面へのフィードバック
    st.success(f'{receiver}さんにメッセージを送りました！')
    
    # ※本来はここでデータベースに書き込みます
    # write(unit, *) sender, receiver, message ... のような感覚です
