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
    # 템플릿에서 사용하는 'author' 필드 추가
    author = db.Column(db.String(50), nullable=False, default='익명')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # 'updated_at' 필드 추가: 수정될 때마다 자동으로 시간이 업데이트됨
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Post {self.id}>'

# -------------------- DB 초기화 (테이블 생성) --------------------
# 앱 컨텍스트 내에서 DB 테이블 생성 실행
with app.app_context():
    # 모델 변경 시에는 기존 test.db를 삭제해야 오류가 발생하지 않습니다.
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
        # 제목 또는 내용에 검색어가 포함된 게시글 필터링
        query = query.filter(
            (Post.title.like(f'%{search_query}%')) | 
            (Post.content.like(f'%{search_query}%'))
        )

    # paginate() 메서드를 사용해 페이지네이션 처리
    posts_pagination = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # pagination 객체와 게시글 데이터를 HTML에 전달
    return render_template('index.html', 
                           posts_pagination=posts_pagination, 
                           posts=posts_pagination.items,
                           search_query=search_query) # 검색어도 템플릿에 전달

# 게시글 상세 조회 (누락되었던 라우트)
@app.route('/post/<int:post_id>')
def post_detail(post_id):
    # post_id를 사용하여 게시글을 데이터베이스에서 조회하거나 404 오류를 반환합니다.
    post = db.get_or_404(Post, post_id)
    return render_template('detail.html', post=post)


# -------------------- 2. CREATE (게시글 작성) --------------------

@app.route('/write', methods=['GET', 'POST'])
def write():
    if request.method == 'POST':
        # 폼에서 데이터 받아오기
        title = request.form['title']
        content = request.form['content']
        author = request.form['author'] # author 필드 처리

        # 새 게시글 객체 생성 및 DB 저장
        new_post = Post(title=title, content=content, author=author)
        try:
            db.session.add(new_post)
            db.session.commit()
            return redirect(url_for('index')) # 저장 후 목록 페이지로 이동
        except Exception as e:
            return f"게시글 작성 중 에러가 발생했습니다: {e}"

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
        post.author = request.form['author'] # author 필드 처리
        # updated_at은 DB 모델 정의에 의해 자동으로 업데이트됩니다.
        
        try:
            db.session.commit()
            return redirect(url_for('post_detail', post_id=post.id)) # 상세 페이지로 이동
        except Exception as e:
            return f"게시글 수정 중 에러가 발생했습니다: {e}"

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
    except Exception as e:
        return f"게시글 삭제 중 에러가 발생했습니다: {e}"


# 서버 실행 (디버그 모드 켜기)
if __name__ == '__main__':
    # host='0.0.0.0'을 추가하여 외부 접근을 허용할 수도 있습니다.
    app.run(debug=True)
