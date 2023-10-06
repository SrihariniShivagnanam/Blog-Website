from flask import Flask, render_template, abort, request, flash, redirect, url_for, session
from flask_admin import Admin, AdminIndexView
from flask_admin import BaseView, expose
from wtforms import form, fields, validators
from flask_sqlalchemy import SQLAlchemy
from flask_admin.contrib.sqla import ModelView
from functools import wraps
import sqlite3
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

def login_required(func):
    @wraps(func)
    def authcheck(*args, **kwargs):
        if not session.get('username'):
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return authcheck

app = Flask(__name__)
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///blog.db"
app.secret_key = "jve%hq8xpzdzdqz136-p=9p_dl5wuz0)p9nos@$&=vq#%i$8*z"
# admin = Admin(app, name='microblog', template_mode='bootstrap3')

con = sqlite3.connect("database.db")
con.execute("create table if not exists users(pid integer primary key,name text,password text,contact integer,mail text)")
con.close()
db = SQLAlchemy(app)

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String, unique=False, nullable=True)
    blog_title = db.Column(db.String, nullable=False)
    blog_content = db.Column(db.Text, nullable=False)
    
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    
    category = relationship('Category', back_populates='blogs')

    def __repr__(self):
        return self.name

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    
    blogs = relationship('Blog', back_populates='category')

    def __repr__(self):
        return self.name

class CustomAdminIndexView(AdminIndexView):
    def is_accessible(self):
        if not session.get('username'):
            return False
        return True


    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))

my_admin = Admin(app, name='microblog', template_mode='bootstrap3', index_view=CustomAdminIndexView())

# class BlogForm(form.Form):
#     blog_title = fields.StringField('Blog Title',validators=[validators.DataRequired()])
#     blog_content = fields.TextAreaField('Blog Content',validators=[validators.DataRequired()])

class BlogModelView(ModelView):

    column_list = ['author', 'blog_title', 'blog_content', 'category']

    form_excluded_columns = ('author')

    def is_accessible(self):
        if not session.get('username'):
            return False
        return True

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))

    def get_query(self):
        if session.get('username'):
            return self.session.query(self.model).filter_by(author=session['username'])
        return self.session.query(self.model).none()

    def on_model_change(self, form, model, is_created):
        if session.get('username'):
            model.author = session['username']


my_admin.add_view(BlogModelView(Blog, db.session))

class CategoryModelView(ModelView):
    form_excluded_columns = ('blogs')

my_admin.add_view(CategoryModelView(Category, db.session))


class HomeAdminView(BaseView):
    @expose('/')
    def index(self):
        return redirect(url_for('blog'))

my_admin.add_view(HomeAdminView(name='Mainpage', endpoint='mainpage'))

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        print(name)
        print(password)
        con = sqlite3.connect("database.db")
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("select * from users where name=? and password=?", (name, password))
        data = cur.fetchone()

        if data:
            session["username"] = data["name"]
            session["password"] = data["password"]
            return redirect("blog")
        else:
            flash("Username and Password Mismatch", "danger")
    return redirect(url_for("index"))

@app.route('/blog', methods=["GET", "POST"])
def blog():
    blogs = Blog.query.all()
    return render_template("blog.html",blogs=blogs)

@app.route('/category/<int:category_id>')
def category_detail(category_id):
    category = Category.query.get(category_id)
    if not category:
        abort(404)  

    blog_posts = Blog.query.filter_by(category_id=category_id).all()

    return render_template('category_detail.html', category=category, blog_posts=blog_posts)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            name = request.form['name']
            password = request.form['password']
            contact = request.form['contact']
            mail = request.form['mail']
            con = sqlite3.connect("database.db")
            cur = con.cursor()
            cur.execute("insert into users(name,password,contact,mail)values(?,?,?,?)", (name, password, contact, mail))
            con.commit()
            flash("Record Added Successfully", "success")
            return redirect(url_for("index"))
        except:
            flash("Error in Insert Operation", "danger")
        finally:
            return redirect(url_for("index"))
            con.close()

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("index"))

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=8001)