from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import extract
from datetime import date

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///engagement.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "secret_key_123"
db = SQLAlchemy(app)

# --- データベース設計 ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), nullable=False)

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    voter_id = db.Column(db.Integer, nullable=False)
    voted_id = db.Column(db.Integer, nullable=False)
    vote_date = db.Column(db.Date, default=date.today)
    comment = db.Column(db.String, nullable=False)

# --- 機能 ---

# 1. ログイン画面
@app.route('/', methods=['GET', 'POST'])
def login_page():
    message = ""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.password == password:
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            return redirect(url_for('vote_page'))
        else:
            message = "名前かパスワードが間違っています"

    return render_template('login.html', message=message)

# 2. 投票画面
@app.route('/vote', methods=['GET', 'POST'])
def vote_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))

    my_id = session['user_id']
    message = ""
    voted = False

    today_vote = Vote.query.filter_by(voter_id=my_id, vote_date=date.today()).first()
    
    if today_vote:
        voted = True
        voted_user = User.query.get(today_vote.voted_id)
        message = f"本日は「{voted_user.username}」さんに投票済みです！"

    if request.method == 'POST' and not voted:
        target_id = request.form['voted_id']
        comment = request.form['comment']
        new_vote = Vote(voter_id=my_id, voted_id=target_id, comment=comment)
        db.session.add(new_vote)
        db.session.commit()
        return redirect(url_for('vote_page'))

    candidates = User.query.filter(User.id != my_id).all()
    # 投票画面にも「ランキングを見る」リンクを渡すためにHTML側で少し工夫してもいいですが、
    # 今回はシンプルにURLを直打ちするか、HTMLにリンクを追加します。
    return render_template('vote.html', name=session['username'], candidates=candidates, message=message, voted=voted)

# 3. ランキング画面
@app.route('/ranking')
def ranking_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    
    if session.get('role') != 'admin':
        return redirect(url_for('vote_page'))
    
    today = date.today()
    first_day = today.replace(day=1) # 今月の1日

    users = User.query.all()
    ranking_data = []
    
    for user in users: # ranking_dataのリスト作成
        if user.role == 'admin_page':
            continue

        count_voted = Vote.query.filter(Vote.voted_id == user.id, Vote.vote_date >= first_day).count()
        count_vote  = Vote.query.filter(Vote.voter_id == user.id, Vote.vote_date >= first_day).count()
        ranking_data.append({'user': user, 'count_voted': count_voted, 'count_vote': count_vote})

    ranking_data.sort(key=lambda x: x['count_voted'], reverse=True)

    return render_template('ranking.html', ranking=ranking_data)
# app.py

@app.route('/ranking/search', methods=['GET', 'POST'])
def ranking_search():
    # --- 1. 管理者チェック（門前払い） ---
    if session.get('role') != 'admin':
        return redirect(url_for('vote_page'))

    ranking_data = []
    search_year = None
    search_month = None

    # --- 2. 検索ボタンが押されたとき(POST)の処理 ---
    if request.method == 'POST':
        # フォームから年と月を受け取る
        search_year = int(request.form.get('year'))
        search_month = int(request.form.get('month'))

        # 全員分ループして集計
        users = User.query.all()
        for u in users:
            if u.role == 'admin':
                continue

            # ★ここがポイント！ 指定した年と月で絞り込む魔法
            vote_count = Vote.query.filter(
                Vote.voted_id == u.id,
                extract('year', Vote.vote_date) == search_year,
                extract('month', Vote.vote_date) == search_month
            ).count()

            # 票があればリストに追加（0票も表示したいなら条件を外す）
            if vote_count > 0:
                ranking_data.append({'user': u, 'count': vote_count})

        # 並べ替え
        ranking_data.sort(key=lambda x: x['count'], reverse=True)

    # --- 3. 画面を表示 ---
    return render_template('ranking_search.html', 
                           ranking=ranking_data, 
                           year=search_year, 
                           month=search_month)

# 4. ログアウト
@app.route('/logout')
def logout_page():
    session.pop('user_id', None)

    return redirect(url_for('login_page'))

# 5. 管理者ページ（一覧・登録）
@app.route('/admin', methods=['GET', 'POST'])
def admin_page():
    # セキュリティ: 管理者(admin)以外は追い出す
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('vote_page'))

    if request.method == 'POST':
        # 新規登録の処理
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        # 同じ名前の人がいないかチェック
        exists = User.query.filter_by(username=username).first()
        if exists:
            # エラー表示などは今回は省略し、ログに出すだけにしておきます
            print("そのユーザー名は既に使われています")
        else:
            new_user = User(username=username, password=password, role=role)
            db.session.add(new_user)
            db.session.commit()
        
        # 画面を更新（二重送信防止のためリダイレクト）
        return redirect(url_for('admin_page'))

    # 全員リストを取得して表示
    all_users = User.query.all()
    return render_template('admin.html', users=all_users)

# 6. メンバー削除機能
@app.route('/admin/delete/<int:id>', methods=['POST'])
def delete_user(id):
    # セキュリティ: 管理者以外は実行不可
    if 'role' not in session or session['role'] != 'admin_page':
        return redirect(url_for('vote_page'))

    # 自分自身を消さないようにする安全装置
    if id == session['user_id']:
        return redirect(url_for('admin_page'))

    user_to_delete = User.query.get(id)
    if user_to_delete:
        db.session.delete(user_to_delete)
        db.session.commit()
    
    return redirect(url_for('admin_page'))

# --- 追加ここまで ---
if __name__ == '__main__':
    app.run(debug=True)
