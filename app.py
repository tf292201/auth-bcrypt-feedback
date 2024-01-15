from flask import Flask, render_template, redirect, flash, session
from flask_debugtoolbar import DebugToolbarExtension
from models import db, connect_db, User, Feedback
from forms import RegisterForm, LoginForm, FeedbackForm

app = Flask(__name__)
app.debug = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///feedback'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'secret'
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
debug = DebugToolbarExtension(app)


connect_db(app)


@app.route('/')
def home():
    return redirect('/register')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register a user: produce form and handle form submission."""
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        
        user = User.register(username, password, email, first_name, last_name)
        db.session.add(user)
        db.session.commit()
        session['username'] = user.username
        flash('Welcome! Successfully Created Your Account!', 'success')
        return redirect(f'/users/{user.username}')
    else:
        return render_template('users/register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Produce login form or handle login."""

    if "username" in session:
        return redirect(f"/users/{session['username']}")

    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)  # <User> or False
        if user:
            session['username'] = user.username
            return redirect(f"/users/{user.username}")
        else:
            form.username.errors = ["Invalid username/password."]
            return render_template("users/login.html", form=form)

    return render_template("users/login.html", form=form)
    
@app.route("/users/<username>")
def show_user(username):
    """logged-in-users page."""

    user = User.query.filter_by(username=username).first()
    feedback = Feedback.query.filter_by(user_id=user.id).all()

    
    return render_template("users/user.html", user=user, feedback=feedback)
    

@app.route('/users/<username>/delete', methods=['POST'])
def delete_user(username):
    """Delete user."""
    if "username" not in session or username != session['username']:
        flash("You must be logged in to view!")
        return redirect("/login")
    user = User.query.filter_by(username=username).first_or_404()
    db.session.delete(user)
    db.session.commit()
    session.pop('username')
    flash('User deleted', 'info')
    return redirect('/login')

@app.route('/logout')
def logout():
    """Logout route."""
    session.pop('username')
    flash('Goodbye!', 'info')
    return redirect('/login')

@app.route('/users/<username>/feedback/add', methods=['GET', 'POST'])
def add_feedback(username):
    """Add feedback for user."""
    if "username" not in session or username != session['username']:
        flash("You must be logged in to view!")
        return redirect("/login")
    form = FeedbackForm()
    user = User.query.filter_by(username=username).first_or_404()
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        feedback = Feedback(title=title, content=content, user_id=user.id)
        db.session.add(feedback)
        db.session.commit()
        flash('Feedback added', 'success')
        return redirect(f'/users/{username}')
    else:
        return render_template('feedback/feedback.html', form=form, user=user)
    
@app.route('/feedback/<int:feedback_id>/update', methods=['GET', 'POST'])
def update_feedback(feedback_id):
    """Update feedback for user."""
    feedback = Feedback.query.get_or_404(feedback_id)
    form = FeedbackForm(obj=feedback)
    if "username" not in session or feedback.user.username != session['username']:
        flash("You must be logged in to view!")
        return redirect("/login")
    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data
        db.session.commit()
        flash('Feedback updated', 'success')
        return redirect(f'/users/{feedback.user.username}')
    else:
        return render_template('/feedback/edit.html', form=form, user=feedback.user, feedback=feedback)
    
@app.route('/feedback/<int:feedback_id>/delete', methods=['POST'])
def delete_feedback(feedback_id):
    """Delete feedback for user."""
    feedback = Feedback.query.get_or_404(feedback_id)
    if "username" not in session or feedback.user.username != session['username']:
        flash("You must be logged in to view!")
        return redirect("/login")
    db.session.delete(feedback)
    db.session.commit()
    flash('Feedback deleted', 'info')
    return redirect(f'/users/{feedback.user.username}')

if __name__ == '__main__':
  app.run()