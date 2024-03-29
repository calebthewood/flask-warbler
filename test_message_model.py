"""Test message model."""
import os
from unittest import TestCase
from models import db, User, Message, Follows, Like
from app import app

# set an environmental variable BEFORE we import our app,
# to use a different database for tests. Do this
# before we import app, since that will have already
# connected to the database
# app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql:///warbler_test"
# os.environ['DB_URI'] = "postgresql:///warbler_test"
# Now we can import app

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DB_TEST_URI']

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

class MessageModelTestCase(TestCase):
    """Test for message model."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        self.uid = 94566
        u = User.signup("testing", "testing@test.com", "password", None)
        u.id = self.uid
        db.session.commit()

        self.u = User.query.get(self.uid)

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_message_model(self):
        """Does basic model work?"""

        m = Message(
            text="a warble",
            user_id=self.uid
        )

        db.session.add(m)
        db.session.commit()

        # User should have 1 message
        self.assertEqual(len(self.u.messages), 1)
        self.assertEqual(self.u.messages[0].text, "a warble")

    def test_message_likes(self):
        m1 = Message(
            text="a warble",
            user_id=self.uid
        )

        m2 = Message(
            text="a very interesting warble",
            user_id=self.uid
        )

        u = User.signup("yetanothertest", "t@email.com", "password", None)
        uid = 888
        u.id = uid
        db.session.add_all([m1, m2, u])
        db.session.commit()

        u.liked_messages.append(m1)

        db.session.commit()

        l = Like.query.filter(Like.user_id == uid).all()
        self.assertEqual(len(l), 1)
        self.assertEqual(l[0].message_id, m1.id)