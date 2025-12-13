from app import app, db, User

# アプリの文脈（コンテキスト）の中で実行する
with app.app_context():
    # もし既にデータがあれば一旦削除してリセット（テスト用）
    db.drop_all()
    db.create_all()

    # テスト用ユーザーの作成
    # User(username="名前", password="パスワード", role="役割")
    user1 = User(username="長尾", password="123", role="ホール")
    user2 = User(username="店長", password="123", role="社員")
    user3 = User(username="キッチンA", password="123", role="キッチン")
    user4 = User(username="バイトB", password="123", role="ホール")

    # データベースに追加するための準備
    db.session.add_all([user1, user2, user3, user4])

    # 変更を確定（コミット）
    db.session.commit()

    print("テスト用データの登録が完了しました！")
