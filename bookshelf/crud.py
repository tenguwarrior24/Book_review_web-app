from bookshelf import get_model
from flask import Blueprint, redirect, render_template, request, url_for, session, flash
from flask_wtf import FlaskForm
from flask_bcrypt import Bcrypt
from flask_login import current_user, login_user, login_required, logout_user
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Length
from sqlalchemy import func, create_engine, and_
from sqlalchemy.orm import Session
from config import SQLALCHEMY_DATABASE_URI


crud = Blueprint('crud', __name__)

class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(),Length(min=4, max=20)])
    password = PasswordField('password', validators =[InputRequired(), Length(min=6, max = 80)])
    remember = BooleanField('Remember Me')

class RegisterForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=20)])
    password = PasswordField('password', validators =[InputRequired(), Length(min=6, max = 80)])

#[START list]
@crud.route("/")
def list():
    token = request.args.get('page_token', None)
    if token:
        token = token.encode('utf-8')
    title = request.args.get('title', None)
    author = request.args.get('author', None)
    search = request.args.get('search', None)
    books, next_page_token = get_model().list(cursor=token)
    model = get_model()
    book_objects = []
    
    if title and author:
        book_objects = model.Book.query.filter(and_(model.Book.title.like('%{}%'.format(title)), model.Book.author.like('%{}%'.format(author)))).all()
        books = []
    elif title:
        book_objects = model.Book.query.filter(model.Book.title.like('%{}%'.format(title))).all()
        books = []
    elif author:
        book_objects = model.Book.query.filter(model.Book.author.like('%{}%'.format(author))).all()
        books = []

    if len(book_objects) > 0: 
        for query in book_objects:
            book = model.from_sql(query)
            books.append(book)

    return render_template(
        "list.html",
        books=books,
        next_page_token=next_page_token,
        search=search
        )
# [END list]



# [START search]
@crud.route("/search", methods=['GET', 'POST'])
def search():
    data = request.form.to_dict(flat=True)
    if request.method == 'POST':
        title = data['title']
        author = data['author']
        return redirect(url_for('.list', title=title, author=author, search=1))
    
    return redirect(url_for('.list'))
# [END search]


@crud.route('/<id>/', methods=['GET', 'POST'])
def view(id):
    book_id = id 
    model = get_model()
    book = model.read_book(book_id)
    engine = create_engine(SQLALCHEMY_DATABASE_URI)
    with Session(engine) as session:
        result = session.query(func.avg(model.Reviews.rating)).filter(model.Reviews.book_id == book_id).scalar()
        review_count = session.query(model.Reviews).filter(model.Reviews.book_id == book_id).count()
        session.close()
        score = '{:.2f}'.format(round(float(result),3) if result else 0.00)
    review = model.read_review(book_id, current_user.id) if current_user.is_authenticated else None

    if request.method == 'POST':
        data = request.form.to_dict(flat=True)
        data['book_id'] = book_id
        data['user_id'] = current_user.id
        review = model.Reviews.query.filter_by(book_id=book_id, user_id=current_user.id).first()
        if review:
            if (int(data['rating'])==0): model.delete_review(book_id, current_user.id)
            else: review = model.update_review(data, book_id, current_user.id)
        else:
            review = get_model().create_review(data)
        return redirect(url_for('.view', id=book['id']))
    return render_template('view.html', book=book, score=score, review=review, review_count=review_count)


# [START add]
@crud.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        data = request.form.to_dict(flat=True)
        book = get_model().create_book(data)
        return redirect(url_for('.view', id=book['id']))
    return render_template("form.html", action="Add", book={})
# [END add]

# [START edit]
@crud.route('/<id>/edit', methods=['GET', 'POST'])
def edit(id):
    book = get_model().read_book(id)
    if request.method == 'POST':
        data = request.form.to_dict(flat=True)
        book = get_model().update(data, id)
        return redirect(url_for('.view', id=book['id']))
    return render_template("form.html", action="Edit", book=book)
# [END edit]


# [START delete]
@crud.route('/<id>/delete')
def delete(id):
    get_model().delete(id)
    return redirect(url_for('.list'))
#[END delete]


#[START register]
@crud.route('/register', methods=['GET','POST'])
def register():
   form = RegisterForm()
   if form.validate_on_submit():
       model = get_model()
       user_data = request.form.to_dict(flat=True)
       model.create_user(user_data)
       return redirect(url_for('.login'))
   return render_template('register.html', form=form)
#[End register]


@crud.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('.list'))
    form = LoginForm()
    if form.validate_on_submit():
        model = get_model()
        user = model.User.query.filter_by(username = form.username.data).first()
        if user:
            if user.password == form.password.data:
                login_user(user)
                return redirect(url_for('.list'))
            else: flash("Login Unsucecssful. Please try again.")
    return render_template('login.html', form=form)


#[LOGOUT]
@crud.route('/logout', methods = ['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('.login'))

