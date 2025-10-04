#기본 설정
from flask import Flask, render_template, request, redirect, url_for, session
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_very_secret_key'

db_config = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'wlsrjsgus1',
    'db': 'myboard',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    """DB 커넥션을 생성하고 반환하는 함수"""
    conn = pymysql.connect(**db_config)
    return conn

#페이지 함수들

@app.route('/') #app.route(''):어떤 함수를 실행할지 연결해주는 역할 
def index():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, author, created_at, views FROM posts ORDER BY created_at DESC")
    posts = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('index.html', posts=posts)

@app.route('/register', methods=['GET', 'POST']) #페이지 접속할때 GET,가입할때 POST
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,)) #똑같은 아이디가 있는지 확인
        user = cursor.fetchone()

        if user:
            return '이미 존재하는 사용자 이름입니다.'

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, hashed_password))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    # (기존 login 함수 코드는 그대로)
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['username'] = user['username']
            return redirect(url_for('index'))
        else:
            return '사용자 이름 또는 비밀번호가 올바르지 않습니다.'
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/write', methods=['GET', 'POST'])
def write():
    # (기존 write 함수 코드는 그대로)
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        author = session['username']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("INSERT INTO posts (title, content, author) VALUES (%s, %s, %s)", (title, content, author))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return redirect(url_for('index'))
    return render_template('board.html')

@app.route('/post/<int:post_id>')
def view_post(post_id):
    # (기존 view_post 함수 코드는 그대로)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE posts SET views = views + 1 WHERE id = %s", (post_id,))
    cursor.execute("SELECT * FROM posts WHERE id = %s", (post_id,))
    post = cursor.fetchone()
    
    conn.commit()
    cursor.close()
    conn.close()
    
    if post is None:
        return "게시글을 찾을 수 없습니다.", 404
        
    return render_template('post_view.html', post=post)

# VVV 수정/삭제 기능이 올바른 위치로 이동했습니다 VVV
@app.route('/post/<int:post_id>/delete')
def delete_post(post_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT author FROM posts WHERE id = %s", (post_id,))
    post = cursor.fetchone()

    if post is None:
        cursor.close()
        conn.close()
        return "게시글을 찾을 수 없습니다.", 404

    if post['author'] != session['username']:
        cursor.close()
        conn.close()
        return "삭제할 권한이 없습니다.", 403

    cursor.execute("DELETE FROM posts WHERE id = %s", (post_id,))
    conn.commit()
    
    cursor.close()
    conn.close()
    
    return redirect(url_for('index'))

@app.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
def edit_post(post_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM posts WHERE id = %s", (post_id,))
    post = cursor.fetchone()

    if post is None:
        cursor.close()
        conn.close()
        return "게시글을 찾을 수 없습니다.", 404

    if post['author'] != session['username']:
        cursor.close()
        conn.close()
        return "수정할 권한이 없습니다.", 403

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        cursor.execute("UPDATE posts SET title = %s, content = %s WHERE id = %s", (title, content, post_id))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('view_post', post_id=post_id))

    cursor.close()
    conn.close()
    return render_template('post_edit.html', post=post)

#서버 실행
if __name__ == '__main__':
    app.run(port=8008, debug=True)