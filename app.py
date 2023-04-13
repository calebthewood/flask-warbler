import os
from dotenv import load_dotenv

from flask import Flask, render_template, request, flash, redirect, session, g
# from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

from forms import CSRFProtectForm, UserAddForm, LoginForm, MessageForm, UserEditForm
from models import db, connect_db, User, Message

CURR_USER_KEY = "curr_user"

load_dotenv()
app = Flask(__name__)

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DB_URI']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
# app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
# toolbar = DebugToolbarExtension(app)

connect_db(app)
db.create_all()

##############################################################################
# User signup/login/logout


@app.before_request
def add_csrf_form():
    """Makes a new CSRF form available before each request"""

    g.csrf_form = CSRFProtectForm()
    g.message_form = MessageForm()


@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])
    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]
    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)
        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)
        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")
        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.post('/logout')
def logout():
    """Handle logout of user."""

    form = g.csrf_form

    if form.validate_on_submit():
        do_logout()
        flash("Log out successful.")

    return redirect("/")


##############################################################################
# General user routes:

@app.get('/users')
def list_users():
    """Return a page with a listing of users.

    If a 'q' parameter is provided in the query string, the function
    will search for usernames containing that parameter.

    Returns:
        str: The HTML for the users listing page.
    """

    search = request.args.get('q')

    if not search:
        users = User.query.all()
    else:
        # case sensitive
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template('users/index.html', users=users)


@app.get('/users/<int:user_id>')
def users_show(user_id: int) -> str:
    """Show a user's profile.

    Retrieves the user with the given ID from the database and renders
    their profile page.

    Args:
        user_id (int): The ID of the user to show.

    Returns:
        str: The HTML for the user's profile page.
    """

    user = User.query.get_or_404(user_id)
    return render_template('users/show.html', user=user)


@app.get('/users/<int:user_id>/following')
def show_following(user_id: int) -> str:
    """Show the list of people that a user is following.

    If the current user is not authenticated, this function will flash an
    error message and redirect to the homepage.

    Args:
        user_id (int): The ID of the user to show the following list for.

    Returns:
        str: The HTML for the list of people the user is following or 404.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/following.html', user=user)


@app.get('/users/<int:user_id>/followers')
def users_followers(user_id: int) -> str:
    """Show the list of followers for a user.

    If the current user is not authenticated, this function will flash an
    error message and redirect to the homepage.

    Args:
        user_id (int): The ID of the user to show the followers for.

    Returns:
        str: The HTML for the list of followers of the user or 404.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/followers.html', user=user)


@app.get('/users/<int:user_id>/liked-messages')
def users_liked_messages(user_id: int) -> str:
    """Show the messages that a user has liked.

    If the current user is not authenticated, this function will flash an
    error message and redirect to the homepage.

    Args:
        user_id (int): The ID of the user to show the liked messages for.

    Returns:
        str: The HTML for the list of messages that the user has liked or 404.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/liked-messages.html', user=user)


@app.post('/users/follow/<int:follow_id>')
def add_follow(follow_id: int) -> str:
    """Add a follow for the currently logged-in user.

    If the current user is not authenticated, this function will flash an
    error message and redirect to the homepage.

    Args:
        follow_id (int): The ID of the user to add a follow for.

    Returns:
        str: A redirect to the page showing the current user's list of followed users or 404.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get_or_404(follow_id)
    g.user.following.append(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.post('/users/stop-following/<int:follow_id>')
def stop_following(follow_id: int) -> str:
    """Have the currently logged-in user stop following another user.

    If the current user is not authenticated, this function will flash an
    error message and redirect to the homepage.

    Args:
        follow_id (int): The ID of the user to stop following.

    Returns:
        str: A redirect to the page showing the current user's list of followed users.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get(follow_id)
    g.user.following.remove(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.route('/users/profile', methods=["GET", "POST"])
def profile():
    """Render user profile edit page, allowing the user to update their profile information.

    If the current user is not logged in, redirect them to the home page.

    GET: Render the user edit form.

    POST: If the form passes validation, update the user's profile and redirect to their profile page. If the password
    entered does not match the user's current password, flash a message and redirect to the edit page.

    Returns:
        If a GET request is made, render the user edit form. If a POST request is made and the form passes validation,
        redirect to the user's profile page.

    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = UserEditForm(obj=g.user)

    if form.validate_on_submit():
        password = form.password.data
        current_username = g.user.username

        if User.authenticate(current_username, password):
            form.populate_obj(g.user)
            db.session.commit()
            return redirect(f"/users/{g.user.id}")
        else:
            flash("Access unauthorized.", "danger")
            return redirect("/")

    return render_template('users/edit.html', form=form)


@app.post('/users/delete')
def delete_user():
    """Delete the current user from the database.

    If no user is logged in, flash a message saying that the access is unauthorized
    and redirect to the home page.

    Logs out the user and removes the user object from the database before
    redirecting to the signup page.

    Returns:
        A redirect response to the signup page.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    do_logout()
    db.session.delete(g.user)
    db.session.commit()

    return redirect("/signup")


##############################################################################
# Messages routes:

@app.route('/messages/new', methods=["GET", "POST"])
def messages_add():
    """Add a new message:

    GET: Display a form to add a new message.
    POST: Process the submitted form. If the form is valid, add the message to the user's list
    of messages and redirect to the user's page.

    Returns:
        If GET: A rendered template with a form to add a new message.
        If POST: A redirect to the user's page if the form is valid.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = MessageForm()

    if form.validate_on_submit():
        msg = Message(text=form.text.data)
        g.user.messages.append(msg)
        db.session.commit()
        return redirect(f"/users/{g.user.id}")

    return render_template('messages/new.html', form=form)


@app.get('/messages/<int:message_id>')
def messages_show(message_id: int) -> str:
    """Display the message with the given message ID.

    Args:
        message_id (int): The ID of the message to display.

    Returns:
        A Flask template with the details of the message and any replies to it.
    """

    msg = Message.query.get(message_id)
    replies = Message.query.filter_by(parent_id=message_id).all()

    if len(replies) > 0:
        msg["replies"] = replies

    return render_template('messages/show.html', message=msg)


@app.post('/messages/<int:message_id>/delete')
def messages_destroy(message_id: int) -> str:
    """Delete a message.

    Only authorized users can delete messages. If the user is not logged in, they
    are redirected to the homepage. Otherwise, the message with the given ID is
    retrieved from the database and deleted. After deletion, the user is redirected
    to their profile page.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    msg = Message.query.get(message_id)
    db.session.delete(msg)
    db.session.commit()
    return redirect(f"/users/{g.user.id}")


@app.post('/messages/<int:message_id>/like')
def add_like(message_id):
    """Add a like for the current user to the specified message.

    If the current user is not logged in, redirect to the homepage with a "danger" flash message.
    Otherwise, add a like from the current user to the specified message and redirect to the homepage.

    Args:
        message_id (int): The ID of the message to like.

    Returns:
        redirect: A redirect to the homepage.

    Raises:
        404: If the specified message is not found in the database.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    message = Message.query.get_or_404(message_id)
    g.user.liked_messages.append(message)
    db.session.commit()
    return redirect("/")


@app.post('/messages/<int:message_id>/unlike')
def remove_like(message_id):
    """Remove a like from a message for the currently logged-in user.

    Returns:
        A redirect to the home page.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    message = Message.query.get_or_404(message_id)
    g.user.liked_messages.remove(message)
    db.session.commit()

    return redirect("/")


##############################################################################
# Homepage and error pages

@app.get('/')
def homepage():
    """Show the homepage.

    If the user is logged in, this view will display the 100 most recent messages
    posted by the current user's followed users and the current user. If the user
    is not logged in, the view will display a page with no messages.

    Returns:
        If the user is logged in, returns a template that displays messages.
        If the user is not logged in, returns a template that does not display messages.
    """
    if g.user:
        user_ids = [user.id for user in g.user.following]
        user_ids.append(g.user.id)
        messages = (Message
                    .query
                    .filter(Message.user_id.in_(user_ids))
                    .order_by(Message.timestamp.desc())
                    .limit(100)
                    .all())
        return render_template('home.html', messages=messages)
    else:
        return render_template('home-anon.html')


##############################################################################
# Turn off all caching in Flask
#   (useful for dev; in production, this kind of stuff is typically
#   handled elsewhere)
#
# https://stackoverflow.com/questions/34066804/disabling-caching-in-flask

@app.after_request
def add_header(response):
    """Add non-caching headers on every request."""

    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control
    response.cache_control.no_store = True
    return response
