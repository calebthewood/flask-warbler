"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DB_TEST_URI']

# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()

    def tearDown(self):
        """Removes all session commits."""
        db.session.rollback()

    def test_add_message(self):
        """Can user add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_messages_destroy(self):
        """Can user delete message?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            #add message for deletion.
            c.post("/messages/new", data={"text": "Hello"})
            msg = Message.query.one()
            #delete added msg.
            resp = c.post(f"/messages/{msg.id}/delete")
            msgs = Message.query.all()

            self.assertEqual(resp.status_code, 302)
            self.assertNotIn(msg, msgs)

    def test_messages_show(self):
        """Tests message display"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            c.post("/messages/new", data={"text": "Testing12345678"})
            msg = Message.query.one()

            resp = c.get(f'/messages/{msg.id}')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Testing12345678", html)

    def test_add_like(self):
        """Tests liking a msg"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            c.post("/messages/new", data={"text": "Hello"})
            msg = Message.query.one()
            u = User.query.get(self.testuser.id)

            resp = c.post(f'/messages/{msg.id}/like')
            msg = Message.query.get(msg.id)

            breakpoint()

            self.assertEqual(resp.status_code, 302)

            self.assertIn(u, msg.users_liked)

            user_ids = [user.id for user in msg.users_liked]

            self.assertIn(self.testuser.id, user_ids)

            #self.assertIs(self.testuser, u)






