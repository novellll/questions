from flask import Flask, render_template, url_for, flash, request, redirect, g
from flask.ext.login import LoginManager, login_user, current_user, logout_user
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from wtforms import StringField, PasswordField, validators
from flask.ext.wtf import Form
app = Flask(__name__)
app.config.update(
    CSRF_ENABLED=True,
    DEBUG=True,
    SECRET_KEY='secret key',
)

# main page view
@app.route('/')
def main_page():
    return render_template('main.html', title='Ask questions - get answers!')

# connecting to DB
engine = create_engine('sqlite:///' + app.root_path + 'questions.db', echo=True)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
# using declarative method
Base = declarative_base()
Base.query = db_session.query_property()


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


# user class
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    password = Column(String)

    def __init__(self, name, password):
        self.name = name
        self.password = password

    def __repr__(self):
        return '<User %s>' % self.name

    def is_active(self):
        return True

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(userid):
    return User.query.get(int(userid))


class LoginForm(Form):
    name = StringField('Login', validators=[validators.DataRequired()])
    password = PasswordField('Password', validators=[validators.DataRequired()])


@app.before_request
def before_request():
    g.user = current_user


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if request.method == 'POST':
        # login and validate the user...
        if form.validate():
            name = request.form['name']
            password = request.form['password']
            user = User.query.filter_by(name=name, password=password).first()
            if user is None:
                flash('Wrong data, try again')
                return redirect(url_for('login'))
            login_user(user)
            flash("Logged in successfully.")
            return redirect(url_for('main_page'))
    return render_template("login_form.html", form=form, title='Sign In')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = LoginForm()
    if request.method == 'POST' and form.validate():
        name = request.form['name']
        password = request.form['password']
        user = User(name, password)
        db_session.add(user)
        db_session.commit()
        flash("You have successfully registered. Now you can log in.")
        return redirect(url_for('login'))
    return render_template('login_form.html', form=form, title='Sign up')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main_page'))


# decelerating models
def init_db():
    Base.metadata.create_all(bind=engine)

init_db()
app.run(debug=True)