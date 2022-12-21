import os

def generate_db_url(db_name = "warbler"):
    """
    Creates DB URL from env vars. Defaults to prod db, pass in 'warbler_test'
    to connect with test db.
    """
    host = os.environ['DB_HOST']
    port = os.environ['DB_PORT']
    user = os.environ['DB_USER']
    pswd = os.environ['DB_PSWD']
    return f"postgresql://{user}:{pswd}@{host}:{port}/{db_name}"
