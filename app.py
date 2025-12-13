from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
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

# --- 機能 ---

# 1. ログイン画面
@app.route('/', methods=['GET', 'POST'])
def login():
    message = ""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.password == password:
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('vote_page'))
        else:
            message = "名前かパスワードが間違っています"

    return render_template('login.html', message=message)

# 2. 投票画面
@app.route('/vote', methods=['GET', 'POST'])
def vote_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))

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
        new_vote = Vote(voter_id=my_id, voted_id=target_id)
        db.session.add(new_vote)
        db.session.commit()
        return redirect(url_for('vote_page'))

    candidates = User.query.filter(User.id != my_id).all()
    # 投票画面にも「ランキングを見る」リンクを渡すためにHTML側で少し工夫してもいいですが、
    # 今回はシンプルにURLを直打ちするか、HTMLにリンクを追加します。
    return render_template('vote.html', name=session['username'], candidates=candidates, message=message, voted=voted)

# 3. ランキング画面（追加機能）
@app.route('/ranking')
def ranking():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    today = date.today()
    first_day = today.replace(day=1) # 今月の1日

    users = User.query.all()
    ranking_data = []
    
    for user in users:
        count = Vote.query.filter(Vote.voted_id == user.id, Vote.vote_date >= first_day).count()
        ranking_data.append({'user': user, 'count': count})

    ranking_data.sort(key=lambda x: x['count'], reverse=True)

    return render_template('ranking.html', ranking=ranking_data)

# 4. ログアウト
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
