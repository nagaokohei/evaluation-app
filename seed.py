from app import app, db, User

# アプリの文脈（コンテキスト）の中で実行する
with app.app_context():
    # もし既にデータがあれば一旦削除してリセット（テスト用）
    db.drop_all()
    db.create_all()
    print("データベースを初期化しました")

    # スタッフ全員のリスト
    staff_members = [
        {"username": "なかがわしんや", "password": "15131", "role": "admin"},
        {"username": "ながおこうへい", "password": "12214", "role": "ホール"},
        {"username": "こんどうあや", "password": "12249", "role": "ホール"},
        {"username": "ほんまひろと", "password": "12255", "role": "ホール"},
        {"username": "きどもえか", "password": "12259", "role": "ホール"},
        {"username": "なみかたまな", "password": "12261", "role": "ホール"},
        {"username": "ちゅうばちりま", "password": "12262", "role": "ホール"},
        {"username": "いがらしはるた", "password": "12266", "role": "ホール"},
        {"username": "さいとうしょうじ", "password": "12276", "role": "ホール"},
        {"username": "くどうこころ", "password": "12277", "role": "ホール"},
        {"username": "ばんばそうた", "password": "12278", "role": "ホール"},
        {"username": "まうらりゅう", "password": "12279", "role": "ホール"},
        {"username": "くまがいたいよう", "password": "12283", "role": "ホール"},
        {"username": "くしびきもにか", "password": "12284", "role": "ホール"},
        {"username": "いしいみう", "password": "12285", "role": "ホール"},
        {"username": "もりななね", "password": "15126", "role": "ホール"},
    ]

    # ループ処理で全員を一括登録
    for member in staff_members:
        user = User(username=member["username"], password=member["password"], role=member["role"])
        db.session.add(user)

    # 変更を確定（コミット）
    db.session.commit()

    print(f"{len(staff_members)}名分のテスト用データの登録が完了しました！")