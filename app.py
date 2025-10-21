# app.py
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Flask 앱 설정
app = Flask(__name__)
# SQLite 데이터베이스 설정 (프로젝트 폴더에 'test.db' 파일로 저장됨)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# -------------------- DB 모델 (게시글 테이블 정의) --------------------
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Post {self.id}>'

# -------------------- DB 초기화 (테이블 생성) --------------------
# 앱 컨텍스트 내에서 DB 테이블 생성 실행
with app.app_context():
    db.create_all()


# app.py (수정할 부분)

# ... 기존 import와 설정 코드들 (변경 없음) ...

# -------------------- 1. READ (게시글 목록 및 상세 조회) --------------------

# 페이지네이션을 위해 /?page=1 형태로 요청을 받을 수 있도록 수정
@app.route('/')
def index():
    # URL 쿼리 파라미터에서 'page' 값을 가져오고, 없으면 기본값은 1
    page = request.args.get('page', 1, type=int)
    per_page = 10  # 페이지당 게시글 수 (10개로 설정)

    # paginate() 메서드를 사용해 페이지네이션 처리
    posts_pagination = Post.query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # pagination 객체와 게시글 데이터를 HTML에 전달
    return render_template('index.html', posts_pagination=posts_pagination, posts=posts_pagination.items)

# -------------------- 2. CREATE (게시글 작성) --------------------

@app.route('/write', methods=['GET', 'POST'])
def write():
    if request.method == 'POST':
        # 폼에서 데이터 받아오기
        title = request.form['title']
        content = request.form['content']

        # 새 게시글 객체 생성 및 DB 저장
        new_post = Post(title=title, content=content)
        try:
            db.session.add(new_post)
            db.session.commit()
            return redirect(url_for('index')) # 저장 후 목록 페이지로 이동
        except:
            return "게시글 작성 중 에러가 발생했습니다."

    return render_template('write.html') # GET 요청 시 글쓰기 폼 표시

# -------------------- 3. UPDATE (게시글 수정) --------------------

@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
def edit(post_id):
    # 수정할 게시글 조회
    post = db.get_or_404(Post, post_id)

    if request.method == 'POST':
        # 폼 데이터로 내용 업데이트
        post.title = request.form['title']
        post.content = request.form['content']
        try:
            db.session.commit()
            return redirect(url_for('post_detail', post_id=post.id)) # 상세 페이지로 이동
        except:
            return "게시글 수정 중 에러가 발생했습니다."

    return render_template('edit.html', post=post) # GET 요청 시 수정 폼 표시

# -------------------- 4. DELETE (게시글 삭제) --------------------

@app.route('/delete/<int:post_id>', methods=['POST'])
def delete(post_id):
    # 삭제할 게시글 조회
    post = db.get_or_404(Post, post_id)
    
    try:
        db.session.delete(post)
        db.session.commit()
        return redirect(url_for('index')) # 삭제 후 목록 페이지로 이동
    except:
        return "게시글 삭제 중 에러가 발생했습니다."


# 서버 실행 (디버그 모드 켜기)
if __name__ == '__main__':
    app.run(debug=True)