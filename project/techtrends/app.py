import sqlite3
import logging

from flask import Flask, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

connection_count = 0


def is_healthy():
    """
    Checks if the app is healthy.

    This function test if:
        - The connection to the database doesn't throw any error.
        - The "posts" table exists.

    Returns:
        True if healthy, otherwise returns false.
    """
    try:
        connection = get_db_connection()
        connection.execute('SELECT id FROM posts;').fetchone()
        connection.close()
        return True
    except Exception as e:
        app.logger.info(e)
        return False


def get_db_connection():
    """Function to get a database connection.

    This function connects to database with the name `database.db`
    """
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    global connection_count
    connection_count += 1

    return connection


def get_post(post_id):
    """Function to get a post using its ID.
    """
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                              (post_id,)).fetchone()
    connection.close()

    return post


def get_all_posts():
    """Function to get all the posts stored in database.
    """
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return posts


def count_posts():
    """Count the total amount of posts in the database.
    """
    return len(get_all_posts())


# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'


@app.route('/')
def index():
    """Define the main route of the web application
    """
    posts = get_all_posts()
    return render_template('index.html', posts=posts)


@app.route('/<int:post_id>')
def post(post_id):
    """Define how each individual article is rendered

    If the post ID is not found a 404 page is shown
    """
    post = get_post(post_id)
    if post is None:
        app.logger.info('Article not found!')
        return render_template('404.html'), 404
    else:
        app.logger.info('Article "{}" retrieved!'.format(post['title']))
        return render_template('post.html', post=post)


@app.route('/about')
def about():
    """Define the About Us page
    """
    app.logger.info('About Us page retrieved')
    return render_template('about.html')


@app.route('/create', methods=('GET', 'POST'))
def create():
    """Define the post creation functionality
    """
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                               (title, content))
            connection.commit()
            connection.close()

            app.logger.info('Article "{}" created!'.format(title))
            return redirect(url_for('index'))

    return render_template('create.html')


@app.route('/healthz')
def healthz():
    """
    Defines the endpoint for Health check.
    """
    message = 'ERROR - unhealthy'
    status = 500

    if is_healthy():
        message = 'OK - healthy'
        status = 200

    return app.response_class(
        response=json.dumps({"result": message}),
        status=status,
        mimetype='application/json'
    )


@app.route('/metrics')
def metrics():
    """Define the metrics endpoint.

    This endpoint will return:
        - Total amount of posts in the database.
        - Total amount of connection to the database.
    """
    response = app.response_class(
        response=json.dumps(
            {'db_connection_count': connection_count, 'post_count': count_posts()}),
        status=200,
        mimetype='application/json'
    )
    return response


# start the application on port 3111
if __name__ == "__main__":
    # stream logs to a file
    logging.basicConfig(
        level=logging.DEBUG, format='%(levelname)s:%(name)s:%(asctime)s, %(message)s', datefmt='%d/%m/%y %H:%M:%S')

    app.run(host='0.0.0.0', port='3111')
