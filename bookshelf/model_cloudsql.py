from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
builtin_list = list


db = SQLAlchemy()


def init_app(app):
    # Disable track modifications, as it unnecessarily uses memory.
    app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)
    db.init_app(app)


def from_sql(row):
    """Translates a SQLAlchemy model instance into a dictionary"""
    data = row.__dict__.copy()
    data['id'] = row.id
    data.pop('_sa_instance_state')
    return data


# [START model]
class Book(db.Model):
    __tablename__ = 'books'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable = False)
    author = db.Column(db.String(255))
    publishedDate = db.Column(db.String(255))
    imageUrl = db.Column(db.String(255))
    description = db.Column(db.String(4096))
    createdBy = db.Column(db.String(255))
    createdById = db.Column(db.String(255))

    def __repr__(self):
        return "<Book(title='%s', author=%s)" % (self.title, self.author)
# [END model]
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(20), nullable =False, unique = True)
    password = db.Column(db.String(80), nullable = False) 
    is_active = db.Column(db.Boolean, default = True)

class Reviews(db.Model):
    __tablename__ = 'reviews'
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'),primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key = True)
    is_favorite = db.Column(db.Boolean, default = 0)
    rating = db.Column(db.Integer)
    review = db.Column(db.String(4096))

# [START list]
def list(limit=10, cursor=None):
    cursor = int(cursor) if cursor else 0
    query = (Book.query
             .order_by(Book.title)
             .limit(limit)
             .offset(cursor))
    books = builtin_list(map(from_sql, query.all()))
    next_page = cursor + limit if len(books) == limit else None
    return (books, next_page)
# [END list]


# [START read]
def read_book(id):
    result = Book.query.get(id)
    if not result:
        return None
    return from_sql(result)
# [END read]

def read_review(book_id, user_id):
    result = Reviews.query.filter_by(book_id=book_id, user_id=user_id).first()
    if result:
        data = result.__dict__.copy()
        data['book_id'] = book_id
        data['user_id'] = user_id
        data.pop('_sa_instance_state', None)
        return data
    else:
        return None


# [START create]
def create_book(data):
    book = Book(**data)
    db.session.add(book)
    db.session.commit()
    return from_sql(book)
# [END create]

def create_user(data):
    del data['csrf_token']
    user = User(**data)
    db.session.add(user)
    db.session.commit()


def create_review(data):
    review = Reviews(**data)
    db.session.add(review)
    db.session.commit()
    data = review.__dict__.copy()
    data.pop('_sa_instance_state', None)
    return data


# [START update]
def update(data, id):
    book = Book.query.get(id)
    for k, v in data.items():
        setattr(book, k, v)
    db.session.commit()
    return from_sql(book)
# [END update]

def update_review(data, book_id, user_id):
    review = Reviews.query.filter_by(book_id=book_id, user_id=user_id).first()
    for k, v in data.items():
        setattr(review, k, v)
    db.session.commit()
    data = review.__dict__.copy()
    data.pop('_sa_instance_state', None)
    return data

def delete(id):
    Book.query.filter_by(id=id).delete()
    db.session.commit()

def delete_review(book_id, user_id):
    Reviews.query.filter_by(book_id=book_id, user_id=user_id).delete()
    db.session.commit()
    
def _create_database():
    """
    If this script is run directly, create all the tables necessary to run the
    application.
    """
    app = Flask(__name__)
    app.config.from_pyfile('../config.py')
    init_app(app)

    with app.app_context():
        db.create_all()
    print("All tables created")


if __name__ == '__main__':
    _create_database()
