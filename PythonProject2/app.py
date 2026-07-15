from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, IntegerField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'champions-edge-ultra-secret-key-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sports_portal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'


# ==========================================
# 1. მონაცემთა ბაზის მოდელები (Models)
# ==========================================

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # football, basketball, etc.
    author = db.Column(db.String(100), default='ადმინისტრატორი')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ==========================================
# 2. ფორმების ვალიდაცია (Flask-WTForms)
# ==========================================

class RegistrationForm(FlaskForm):
    first_name = StringField('სახელი', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('გვარი', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('ელფოსტა', validators=[DataRequired(), Email()])
    age = IntegerField('ასაკი', validators=[DataRequired()])
    password = PasswordField('პაროლის შექმნა', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('გაიმეორეთ პაროლი', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('რეგისტრაცია')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('ეს ელფოსტა უკვე გამოყენებულია! სცადეთ სხვა.')


class LoginForm(FlaskForm):
    email = StringField('ელფოსტა', validators=[DataRequired(), Email()])
    password = PasswordField('პაროლი', validators=[DataRequired()])
    submit = SubmitField('შესვლა')


class PostForm(FlaskForm):
    title = StringField('პოსტის სათაური', validators=[DataRequired()])
    category = StringField('სპორტის სახეობა (მაგ. კალათბურთი, UFC...)', validators=[DataRequired()])
    content = TextAreaField('დეტალური ინფორმაცია', validators=[DataRequired(), Length(min=10)])
    submit = SubmitField('პოსტის გამოქვეყნება')


# ==========================================
# 3. როუტები (Routes) & ლოგიკა
# ==========================================

@app.route('/')
def index():
    posts = Post.query.order_by(Post.id.desc()).all()
    return render_template('index.html', posts=posts)



@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        # ვიყენებთ უსაფრთხო ჰაშირებას მეთოდის პარამეტრის გარეშე (თანამედროვე Werkzeug-ისთვის)
        hashed_pw = generate_password_hash(form.password.data)
        user = User(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            age=form.age.data,
            password=hashed_pw
        )
        db.session.add(user)
        db.session.commit()
        flash('რეგისტრაცია წარმატებით დასრულდა! შეგიძლიათ გაიაროთ ავტორიზაცია.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('ავტორიზაცია წარმატებულია! კეთილი იყოს თქვენი მობრძანება.', 'success')
            return redirect(url_for('index'))
        else:
            flash('მონაცემები არასწორია. გთხოვთ, შეამოწმოთ ელფოსტა და პაროლი.', 'danger')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('თქვენ გამოხვედით სისტემიდან.', 'info')
    return redirect(url_for('index'))


@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if not current_user.is_admin:
        flash('ამ გვერდზე წვდომა მხოლოდ ადმინისტრატორებს აქვთ!', 'danger')
        return redirect(url_for('index'))

    form = PostForm()
    if form.validate_on_submit():
        new_post = Post(
            title=form.title.data,
            category=form.category.data,
            content=form.content.data,
            author=f"{current_user.first_name} {current_user.last_name}"
        )
        db.session.add(new_post)
        db.session.commit()
        flash('ახალი პოსტი წარმატებით დაემატა საიტზე!', 'success')
        return redirect(url_for('index'))





    return render_template('admin.html', form=form)




# ==========================================
# 4. სპორტული გვერდების როუტინგი
# ==========================================

@app.route('/basketball')
@login_required
def basketball():
    return render_template('basketball.html')


@app.route('/basketball/nba')
@login_required
def nba():
    # NBA-ს 20 საუკეთესო მოთამაშის სრული რეიტინგი და სტატისტიკა
    players = [
        {"rank": 1, "name": "Nikola Jokić", "team": "DEN", "ppg": 26.4, "rpg": 12.4, "apg": 9.0, "mvp": "85%"},
        {"rank": 2, "name": "Luka Dončić", "team": "DAL", "ppg": 33.9, "rpg": 9.2, "apg": 9.8, "mvp": "72%"},
        {"rank": 3, "name": "Shai Gilgeous-Alexander", "team": "OKC", "ppg": 30.1, "rpg": 5.5, "apg": 6.2,
         "mvp": "68%"},
        {"rank": 4, "name": "Giannis Antetokounmpo", "team": "MIL", "ppg": 30.4, "rpg": 11.5, "apg": 6.5, "mvp": "40%"},
        {"rank": 5, "name": "Jayson Tatum", "team": "BOS", "ppg": 26.9, "rpg": 8.1, "apg": 4.9, "mvp": "15%"},
        {"rank": 6, "name": "Joel Embiid", "team": "PHI", "ppg": 34.7, "rpg": 11.0, "apg": 5.6, "mvp": "10%"},
        {"rank": 7, "name": "Kevin Durant", "team": "PHX", "ppg": 27.1, "rpg": 6.6, "apg": 5.0, "mvp": "5%"},
        {"rank": 8, "name": "Anthony Davis", "team": "LAL", "ppg": 24.7, "rpg": 12.6, "apg": 3.5, "mvp": "2%"},
        {"rank": 9, "name": "Devin Booker", "team": "PHX", "ppg": 27.1, "rpg": 4.5, "apg": 6.9, "mvp": "1%"},
        {"rank": 10, "name": "Anthony Edwards", "team": "MIN", "ppg": 25.9, "rpg": 5.4, "apg": 5.1, "mvp": "1%"},
        {"rank": 11, "name": "Stephen Curry", "team": "GSW", "ppg": 26.4, "rpg": 4.5, "apg": 5.1, "mvp": "0%"},
        {"rank": 12, "name": "LeBron James", "team": "LAL", "ppg": 25.7, "rpg": 7.3, "apg": 8.3, "mvp": "0%"},
        {"rank": 13, "name": "Domantas Sabonis", "team": "SAC", "ppg": 19.4, "rpg": 13.7, "apg": 8.2, "mvp": "0%"},
        {"rank": 14, "name": "Jalen Brunson", "team": "NYK", "ppg": 28.7, "rpg": 3.6, "apg": 6.7, "mvp": "0%"},
        {"rank": 15, "name": "Kawhi Leonard", "team": "LAC", "ppg": 23.7, "rpg": 6.1, "apg": 3.6, "mvp": "0%"},
        {"rank": 16, "name": "Tyrese Haliburton", "team": "IND", "ppg": 20.1, "rpg": 3.9, "apg": 10.9, "mvp": "0%"},
        {"rank": 17, "name": "Donovan Mitchell", "team": "CLE", "ppg": 26.6, "rpg": 5.1, "apg": 6.1, "mvp": "0%"},
        {"rank": 18, "name": "De'Aaron Fox", "team": "SAC", "ppg": 26.6, "rpg": 4.6, "apg": 5.6, "mvp": "0%"},
        {"rank": 19, "name": "Bam Adebayo", "team": "MIA", "ppg": 19.3, "rpg": 10.4, "apg": 3.9, "mvp": "0%"},
        {"rank": 20, "name": "Tyrese Maxey", "team": "PHI", "ppg": 25.9, "rpg": 3.7, "apg": 6.2, "mvp": "0%"}
    ]
    return render_template('nba.html', players=players)


@app.route('/basketball/euroleague')
@login_required
def euroleague():
    return render_template('euroleague.html')


@app.route('/basketball/eurobasket')
@login_required
def eurobasket():
    return render_template('eurobasket.html')


@app.route('/basketball/worldcup')
@login_required
def worldcup_basket():
    return render_template('worldcup_basket.html')


@app.route('/football')
@login_required
def football():
    return render_template('football.html')


# ფეხბურთის ტოპ ლიგების როუტები
@app.route('/football/bundesliga')
@login_required
def bundesliga():
    return render_template('league_bundesliga.html')


@app.route('/football/laliga')
@login_required
def laliga():
    return render_template('league_laliga.html')


@app.route('/football/ligue1')
@login_required
def ligue1():
    return render_template('league_ligue1.html')


@app.route('/football/premierleague')
@login_required
def premierleague():
    return render_template('league_premierleague.html')


@app.route('/football/seriea')
@login_required
def seriea():
    return render_template('league_seriea.html')


@app.route('/football/worldcup')
@login_required
def worldcup_football():
    return render_template('league_worldcup.html')


@app.route('/ufc')
@login_required
def ufc():
    return render_template('ufc.html')


@app.route('/judo')
@login_required
def judo():
    return render_template('judo.html')


@app.route('/boxing')
@login_required
def boxing():
    return render_template('boxing.html')


@app.route('/national-achievements')
@login_required
def national():
    return render_template('national.html')


# ==========================================
# 5. მონაცემთა ბაზის ინიციალიზაცია
# ==========================================

def init_db():
    with app.app_context():
        db.create_all()
        # ავტომატურად ვქმნით ადმინს საწყისი ტესტირებისთვის
        if not User.query.filter_by(email="admin@sports.ge").first():
            hashed_pw = generate_password_hash("admin123")
            admin_user = User(
                first_name="სისტემის",
                last_name="ადმინი",
                email="admin@sports.ge",
                age=25,
                password=hashed_pw,
                is_admin=True
            )
            db.session.add(admin_user)
            db.session.commit()


if __name__ == '__main__':
    init_db()
    app.run(debug=True,host='0.0.0.0')