from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

# Flask 앱 설정
app = Flask(__name__)

# -------------------- DB 설정 (Render PostgreSQL 환경 변수 사용) --------------------
# Render 환경에서 제공하는 DATABASE_URL 환경 변수를 가져옵니다.
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # Render는 'postgres://'를 제공하지만, SQLAlchemy는 'postgresql://' 형식을 요구합니다.
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    # 📌 PostgreSQL 연결 설정
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    
    # Render의 PostgreSQL은 SSL 연결을 요구하므로 엔진 옵션을 추가합니다.
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "connect_args": {
            "sslmode": "require"
        }
    }
else:
    # 📌 로컬 개발 환경을 위한 SQLite 설정 (배포 환경에서는 사용되지 않음)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# -------------------- DB 모델 (게시글 테이블 정의) --------------------
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(50), nullable=False, default='익명')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Post {self.id}>'

# -------------------- DB 초기화 (테이블 생성) --------------------
# 앱 컨텍스트 내에서 DB 테이블 생성 실행
with app.app_context():
    # PostgreSQL 사용 시, 기존의 test.db 삭제가 필요 없습니다.
    # PostgreSQL에 테이블이 존재하지 않으면 새로 생성됩니다.
    db.create_all()


# -------------------- 1. READ (게시글 목록 및 상세 조회) --------------------

@app.route('/')
def index():
    # 검색어 처리
    search_query = request.args.get('search_query', '')
    
    # URL 쿼리 파라미터에서 'page' 값을 가져오고, 없으면 기본값은 1
    page = request.args.get('page', 1, type=int)
    per_page = 10  # 페이지당 게시글 수 (10개로 설정)

    # 쿼리 필터링
    query = Post.query.order_by(Post.created_at.desc())
    
    if search_query:
        # PostgreSQL은 COLLATE NOCASE를 지원하지 않으므로, 
        # 검색 시 LIKE 쿼리를 사용합니다.
        query = query.filter(
            (Post.title.like(f'%{search_query}%')) | 
            (Post.content.like(f'%{search_query}%'))
        )

    # paginate() 메서드를 사용해 페이지네이션 처리
    posts_pagination = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('index.html', 
                           posts_pagination=posts_pagination, 
                           posts=posts_pagination.items,
                           search_query=search_query) 

# 게시글 상세 조회
@app.route('/post/<int:post_id>')
def post_detail(post_id):
    post = db.get_or_404(Post, post_id)
    return render_template('detail.html', post=post)


# -------------------- 2. CREATE (게시글 작성) --------------------

@app.route('/write', methods=['GET', 'POST'])
def write():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        author = request.form['author']

        new_post = Post(title=title, content=content, author=author)
        try:
            db.session.add(new_post)
            db.session.commit()
            return redirect(url_for('index'))
        except Exception as e:
            # 에러 발생 시 상세 메시지 출력
            return f"게시글 작성 중 에러가 발생했습니다: {e}"

    return render_template('write.html')

# -------------------- 3. UPDATE (게시글 수정) --------------------

@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
def edit(post_id):
    post = db.get_or_404(Post, post_id)

    if request.method == 'POST':
        post.title = request.form['title']
        post.content = request.form['content']
        post.author = request.form['author']
        
        try:
            db.session.commit()
            return redirect(url_for('post_detail', post_id=post.id))
        except Exception as e:
            return f"게시글 수정 중 에러가 발생했습니다: {e}"

    return render_template('edit.html', post=post)

# -------------------- 4. DELETE (게시글 삭제) --------------------

@app.route('/delete/<int:post_id>', methods=['POST'])
def delete(post_id):
    post = db.get_or_404(Post, post_id)
    
    try:
        db.session.delete(post)
        db.session.commit()
        return redirect(url_for('index'))
    except Exception as e:
        return f"게시글 삭제 중 에러가 발생했습니다: {e}"


# 서버 실행 (로컬 환경에서만 debug=True)
if __name__ == '__main__':
    app.run(debug=True)
