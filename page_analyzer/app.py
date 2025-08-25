import os
import psycopg2
import validators
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv



load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')


def connect_db():
	return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


@app.route('/')
def index():
	return render_template('main.html')


@app.route('/urls', methods=['POST'])
def add_url():
	url = request.form.get('url')
	if not validators.url(url):
		flash('Некорректный URL', 'alert alert-danger')
		return redirect(url_for('index'))

	parsed_url = urlparse(url)
	normalized_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

	try:
		conn = connect_db()
		cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
		cur.execute("SELECT * FROM urls WHERE name = %s", (normalized_url,))
		existing_url = cur.fetchone()

		if existing_url:
			url_id = existing_url['id']
			flash('Страница уже существует', 'alert alert-info')
		else:
			cur.execute("INSERT INTO urls (name, created_at) VALUES (%s, %s) RETURNING id",
		                (normalized_url, datetime.utcnow())
		                )
			url_id = cur.fetchone()['id']
			conn.commit()
			flash('Страница успешно добавлена', 'alert alert-success')

		cur.close()
		conn.close()
		return redirect(url_for('url_detail', id=url_id))
	except Exception as e:
		flash(f'Ошибка сервера: {str(e)}', 'alert alert-danger')
		return redirect(url_for('index'))


@app.route('/urls')
def urls_list():
	conn = connect_db()
	cur = conn.cursor()
	cur.execute("SELECT * FROM urls ORDER BY id DESC")
	urls = cur.fetchall()
	cur.close()
	conn.close()
	return render_template('urls.html', url_list=urls)


@app.route('/urls/<int:id>')
def url_detail(id):
	conn = connect_db()
	cur = conn.cursor()
	cur.execute("SELECT * FROM urls WHERE id = %s", (id,))
	url = cur.fetchone()
	if not url:
		flash('URL не найден', 'alert alert-danger')
		cur.close()
		conn.close()
		return redirect(url_for('urls_list'))
	cur.execute("""
	       SELECT id, created_at
	       FROM url_checks
	       WHERE url_id = %s
	       ORDER BY id DESC
	   """, (id,))
	checks = cur.fetchall()
	cur.close()
	conn.close()
	return render_template(
		'url_details.html',
		url_id=url['id'],
		url_name=url['name'],
		url_created_at=url['created_at'],
		checks=checks,
		id=id
	)


@app.route('/urls/<id>/checks', methods=['POST'])
def url_checks(id):
	conn = connect_db()
	cur = conn.cursor(cursor_factory=RealDictCursor)
	cur.execute(
		"INSERT INTO url_checks (url_id, created_at) VALUES (%s, %s) RETURNING id;",
		(id, datetime.now())
	)
	conn.commit()
	cur.close()
	conn.close()
	flash("Страница успешно проверена", "alert alert-success")
	return redirect(url_for('url_detail', id=id))