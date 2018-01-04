from flask import Flask, g, render_template, flash, redirect, url_for, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import check_password_hash
from forms import *
import models 

DEBUG = True
PORT = 8000
HOST = '127.0.0.1'

app = Flask(__name__)
app.secret_key = "\xf4Vu\xdcF\r\xa3\xa8\x1b(9e\xf6g2\x06\x90\x96\x9f\x8c]\xee\x13\xb9"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(userid):
    try:
        return models.User.get(models.User.id == userid)
    except models.DoesNotExist:
        return None

@app.before_request
def before_request():
    """Connect to the database before each request."""
    g.db = models.DATABASE
    g.db.connect()
    g.user = current_user


@app.after_request
def after_request(response):
    """Close the database connection after each request."""
    g.db.close()
    return response


@app.route('/register/', methods=['GET','POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        flash("Yay! you registered!", "success")
        models.User.create_user(
            username = form.username.data,
            email = form.email.data,
            password = form.password.data
        )
        return redirect(url_for('index'))
    return render_template('register.html', form=form)


@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404


@app.route('/login/', methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = models.User.get(models.User.email == form.email.data)
        except models.DoesNotExist:
            flash("Your Email or Password doesn't match", "error")
        else:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                flash("You've been logged in!", "success")
                return redirect(url_for('index'))
            else:
                flash("Your Email or Password doesn't match", "error")
    return render_template("login.html", form=form)
                

@app.route('/')
def index():
    stream = models.Post.select().limit(100)
    return render_template("stream.html", stream=stream)


@app.route("/stream/")
@app.route("/stream/<username>/")
def stream(username=None):
    template = "stream.html"
    if username and username != current_user.username:
        try:
            user = models.User.select().where(models.User.username**username).get()
            stream = user.posts.limit(100)
        except models.DoesNotExist:
            abort(404)
    else:
        stream = current_user.get_stream().limit(100)
        user = current_user
    if username:
        template = "user_stream.html"
    return render_template(template, stream=stream, user=user)


@app.route('/post/<int:post_id>/')
def view_post(post_id):
    posts = models.Post.select().where(models.Post.id == post_id)
    if posts.count() == 0:
        abort(404)
    return render_template("stream.html", stream=posts)

@app.route('/logout/')
@login_required
def logout():
    logout_user()
    flash("You've been logged out! Come back soon.", "success")
    return redirect(url_for('login'))


@app.route('/post_form', methods=['GET','POST'])
@login_required
def post():
    form = PostForm()
    if form.validate_on_submit():
        models.Post.create(
            user = g.user._get_current_object(), 
            content = form.content.data.strip()
        )
        flash("Message posted! Thanks!", "success")
        return redirect(url_for('index'))
    return render_template("post.html", form=form)



@app.route('/follow/<username>/')
@login_required
def follow(username):
    try:
        to_user = models.User.get(models.User.username**username)
    except models.DoesNotExist:
        abort(404)
    else:
        try:
            models.Relationship.create(from_user=g.user._get_current_object(), to_user=to_user)
        except models.IntegrityError:
            pass
        else:
            flash("You're now following {}!".format(to_user.username), "success")
    return redirect(url_for('stream', username=to_user.username))


@app.route('/unfollow/<username>/')
@login_required
def unfollow(username):
    try:
        to_user = models.User.get(models.User.username**username)
    except models.DoesNotExist:
        abort(404)
    else:
        try:
            models.Relationship.get(from_user=g.user._get_current_object(), to_user=to_user).delete_instance()
        except models.IntegrityError:
            pass
        else:
            flash("You've unfollowed {}!".format(to_user.username), "success")
    return redirect(url_for('stream', username=to_user.username))


if __name__ == '__main__':
    models.initialize()
    try:
        models.User.create_user(
            username='shubham',
            email='shubham@gmail.com',
            password='pass1234',
            admin=True
        )
    except ValueError:
        pass
    app.run(debug=DEBUG, host=HOST, port=PORT)