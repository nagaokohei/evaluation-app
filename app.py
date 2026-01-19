from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import extract
from datetime import datetime, timedelta

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
    voter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    voted_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    vote_date = db.Column(db.DateTime, default=datetime.now)
    comment = db.Column(db.String, nullable=False)
    voter = db.relationship('User', foreign_keys=[voter_id], backref='sent_votes')
    voted = db.relationship('User', foreign_keys=[voted_id], backref='received_votes')

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

    now = datetime.now()

    # 2. 「現在の営業日」の開始時間（朝4時）を計算
    if now.hour < 4:
        # 深夜（0時〜3時）なら、「昨日」の朝4時からが今日の営業範囲
        start_time = (now - timedelta(days=1)).replace(hour=4, minute=0, second=0, microsecond=0)
    else:
        # 朝4時を過ぎていれば、「今日」の朝4時から
        start_time = now.replace(hour=4, minute=0, second=0, microsecond=0)

    # 3. 終了時間（次の日の朝4時）
    end_time = start_time + timedelta(days=1)

    # 4. データベース検索（範囲指定に変える）
    # ※ filter_by ではなく filter を使い、不等号で挟みます
    today_vote = Vote.query.filter(
        Vote.voter_id == my_id,       # 自分かどうか
        Vote.vote_date >= start_time, # 営業開始より後
        Vote.vote_date < end_time     # 営業終了より前
    ).first()

    if today_vote:
        voted = True
        voted_user = User.query.get(today_vote.voted_id)
        message = f"本日は「{voted_user.username}」さんに投票済みです！"
        return render_template('vote.html', name=session['username'], candidates=[], message=message, voted=voted)  

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


@app.route('/history')
def history():
    # 1. ログインチェック
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user_id = session['user_id']

    # --- 2. 「今日すでに投票したか？」のチェック (4時区切り) ---
    now = datetime.now()
    if now.hour < 4:
        start_time = (now - timedelta(days=1)).replace(hour=4, minute=0, second=0, microsecond=0)
    else:
        start_time = now.replace(hour=4, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(days=1)

    # 今日の投票データを探す
    today_vote = Vote.query.filter(
        Vote.voter_id == user_id,
        Vote.vote_date >= start_time,
        Vote.vote_date >= start_time,
    ).first()

    # ★もし投票していなければ、投票画面へ強制送還
    if not today_vote:
        flash("履歴を見るには、本日の投票を完了してください！")
        return redirect(url_for('vote_page'))

    # --- 3. 履歴データの取得 ---
    
    # 受信履歴 (自分が voted_id になっているもの)
    received_votes = Vote.query.filter_by(voted_id=user_id).order_by(Vote.vote_date.desc()).all()
    
    # 送信履歴 (自分が voter_id になっているもの)
    sent_votes = Vote.query.filter_by(voter_id=user_id).order_by(Vote.vote_date.desc()).all()

    return render_template('history.html', received=received_votes, sent=sent_votes)

# 3. ランキング画面
@app.route('/ranking')
def ranking_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    
    if session.get('role') != 'admin':
        return redirect(url_for('vote_page'))
    
    today = datetime.now()
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

# 4. 集計結果検索画面
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
        cutoff_hour = 4 

        # 1. 検索したい月の「開始日時」を作る (例: 1月1日 04:00:00)
        start_dt = datetime(search_year, search_month, 1, cutoff_hour, 0, 0)

        # 2. 「翌月の開始日時」を作る（＝検索したい月の終了日時）
        # 12月の場合は、翌年は「来年の1月」になるよう調整が必要
        if search_month == 12:
            next_year = search_year + 1
            next_month = 1
        else:
            next_year = search_year
            next_month = search_month + 1
            
        # 例: 2月1日 03:59:59 まで（厳密には 04:00:00 未満）
        end_dt = datetime(next_year, next_month, 1, cutoff_hour, 0, 0)

        # 3. データベース検索（extractをやめて、期間指定にする）
        users = User.query.all()
        for u in users:
            if u.role == 'admin':
                continue

            # filter で挟み撃ち (start <= timestamp < end)
            vote_count = Vote.query.filter(
                Vote.voted_id == u.id,
                Vote.vote_date >= start_dt, # 開始日時以上
                Vote.vote_date < end_dt     # 終了日時より前
            ).count()

            if vote_count > 0:
                ranking_data.append({'user': u, 'count': vote_count})
        
        ranking_data.sort(key=lambda x: x['count'], reverse=True)

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
