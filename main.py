import os
from socket import gethostname
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask import Flask, render_template, redirect, request, abort, url_for
from flask_restful import abort, Api
from PIL import Image
from data.login_form import LoginForm
from data.news_form import NewsForm
from data.dialog_form import DialogForm
from data.dialogs import Dialogs
from data.users import User
from data.news import News
from data.register_form import RegisterForm
from data import db_session, news_resources

app = Flask(__name__)
api = Api(app)
UPLOAD_FOLDER = 'static/img'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'gif', 'jpeg'}
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
login_manager = LoginManager()
login_manager.init_app(app)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def get_file_format(file):
    return str(file)[str(file).find('.'):str(file).find('.') + 4]


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route("/")
def index():
    session = db_session.create_session()
    news = session.query(News).filter(News.is_private != True)
    if current_user.is_authenticated:
        news = session.query(News).filter(
            (News.user == current_user) | (News.is_private != True))
    else:
        news = session.query(News).filter(News.is_private != True)
    return render_template("index.html", news=news)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        session = db_session.create_session()
        if session.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такая почта уже зарегистрирована")
        user = User(name=form.name.data, email=form.email.data, about=form.about.data, image='no.png')
        user.set_password(form.password.data)
        session.add(user)
        session.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/news/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    form = NewsForm()
    if request.method == "GET":
        session = db_session.create_session()
        news = session.query(News).filter(News.id == id, News.user == current_user).first()
        if news:
            form.title.data = news.title
            form.content.data = news.content
            form.is_private.data = news.is_private
        else:
            abort(404)
    if form.validate_on_submit():
        session = db_session.create_session()
        news = session.query(News).filter(News.id == id,
                                          News.user == current_user).first()
        if news:
            news.title = form.title.data
            news.content = form.content.data
            news.is_private = form.is_private.data
            file = request.files['file']
            if file and allowed_file(file.filename):
                file.save(os.path.join('static/other_img', str(news.id) + get_file_format(file)))
                image = Image.open('static/other_img/' + str(news.id) + get_file_format(file))
                image_size = [image.width, image.height]
                if 720 / image_size[0] > 576 / image_size[1]:
                    image.thumbnail((image_size[0] * image_size[1] / 576, 576), Image.ANTIALIAS)
                else:
                    image.thumbnail((720, image_size[1] * image_size[0] / 720), Image.ANTIALIAS)
                image.save(os.path.join('static/other_img', str(news.id) + get_file_format(file)))
                news.image = str(news.id) + get_file_format(file)
            session.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('news.html', title='Редактирование новости', form=form)


@app.route('/news_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def news_delete(id):
    session = db_session.create_session()
    news = session.query(News).filter(News.id == id, News.user == current_user).first()
    if news:
        if news.image:
            os.remove('static/other_img/' + news.image)
        session.delete(news)
        session.commit()
    else:
        abort(404)
    return redirect('/')


@app.route('/news', methods=['GET', 'POST'])
@login_required
def add_news():
    form = NewsForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        news = News()
        news.title = form.title.data
        news.content = form.content.data
        news.is_private = form.is_private.data
        current_user.news.append(news)
        session.merge(current_user)
        session.commit()
        session = db_session.create_session()
        file = request.files['file']
        if file and allowed_file(file.filename):
            new = session.query(News)[-1]
            file.save(os.path.join('static/other_img', str(new.id) + get_file_format(file)))
            image = Image.open('static/other_img/' + str(new.id) + get_file_format(file))
            image_size = [image.width, image.height]
            if 720 / image_size[0] > 576 / image_size[1]:
                image.thumbnail((image_size[0] * image_size[1] / 576, 576), Image.ANTIALIAS)
            else:
                image.thumbnail((720, image_size[1] * image_size[0] / 720), Image.ANTIALIAS)
            image.save(os.path.join('static/other_img', str(new.id) + get_file_format(file)))
            new.image = str(new.id) + get_file_format(file)
            session.commit()
        return redirect('/')
    return render_template('news.html', title='Добавление новости',
                           form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/user_profile/<userid>', methods=['GET', 'POST'])
def user_profile(userid):
    session = db_session.create_session()
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            for elem in list(filter(lambda x: x[:len(userid)] == userid, [i for i in os.listdir(path="static/img/")])):
                os.remove(f'static/img/{elem}')
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], userid + get_file_format(file)))
            session.query(User).filter(User.id == current_user.id).first().image = userid + get_file_format(file)
            session.commit()
    news = session.query(News).filter(News.user_id == userid)
    user = session.query(User).filter(User.id == userid).first()
    if userid not in [i.split('.')[0] for i in os.listdir(path="static/img/")]:
        img = url_for('static', filename='img/no.png')
    else:
        img = url_for('static', filename=f'img/{userid}{get_file_format(user.image)}')
    return render_template("profile.html", iimg=img, news=news, user=user)


@app.route('/dialog/<userid>', methods=['GET', 'POST'])
def dialog_with(userid):
    form = DialogForm()
    session = db_session.create_session()
    if form.validate_on_submit():
        user = session.query(User).filter(User.id == current_user.id).first()
        if user.dialogs_with is not None:
            if userid not in current_user.dialogs_with:
                user.dialogs_with += '&' + str(userid)
        else:
            user.dialogs_with = str(userid)

        user = session.query(User).filter(User.id == userid).first()
        if user.dialogs_with is not None:
            if str(current_user.id) not in user.dialogs_with:
                user.dialogs_with += '&' + str(current_user.id)
        else:
            user.dialogs_with = str(current_user.id)
        title = '&'.join([str(i) for i in sorted([int(current_user.id), int(userid)])])
        if form.content.data != '':
            dia = Dialogs()
            dia.text = form.content.data
            form.content.data = ''
            dia.users_id = title
            dia.user_id = current_user.id
            session.add(dia)
            session.commit()
    dialog = session.query(Dialogs).filter(
        Dialogs.users_id == '&'.join([str(i) for i in sorted([int(userid), int(current_user.id)])]))
    return render_template('dialog.html', dialog=dialog, form=form)


@app.route('/dialogs')
def dialogs():
    users = []
    session = db_session.create_session()
    if current_user.dialogs_with is not None:
        for i in current_user.dialogs_with.split('&'):
            users.append(session.query(User).filter(User.id == int(i)).first())
    return render_template('dialogs.html', dialogs=users)


def main():
    db_session.global_init("db/blogs.sqlite")
    api.add_resource(news_resources.NewsListResource, '/api/news')
    api.add_resource(news_resources.NewsResource, '/api/news/<int:news_id>')
    app.run()


if __name__ == '__main__':
    main()
