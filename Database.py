import sqlite3
import os

import config

DATABASE = config.databaseFile
INIT_SCRIPT = """
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS posts;
DROP TABLE IF EXISTS comments;
DROP TABLE IF EXISTS responses;
DROP TABLE IF EXISTS bookInformation;
DROP TABLE IF EXISTS authorInformation;

CREATE TABLE users (
	userId text primary key not null
);

CREATE TABLE messages (
	messageId text primary key not null,
	timestamp integer,
	read integer
);

CREATE TABLE posts (
	postId text primary key not null,
	timestamp integer
);

CREATE TABLE comments (
	commentId text primary key not null,
	timestamp integer,
	postId text not null
);

CREATE TABLE response (
);

CREATE TABLE bookInformation (
	bid integer primary key not null
);

CREATE TABLE authorInformation (
	aid integer primary key not null
);
"""

cwd = os.path.dirname(os.path.abspath(__file__))

# Util methods
def get_db(database):
	db = sqlite3.connect(cwd + "/" + database)
	db.row_factory = sqlite3.Row
	return db

def query_db(db, query, args=(), one=False):
	cur = db.execute(query, args)
	rv = cur.fetchall()
	cur.close()
	return (rv[0] if rv else None) if one else rv

def init_db(database):
	db = get_db(database)
	db.cursor().executescript(INIT_SCRIPT)

if __name__ == '__main__':
	init_db(DATABASE)

# Message Methods
def insertMessage(db, messageId, timestamp):
	db.cursor().execute("INSERT INTO messages VALUES (?, ?)", (messageId, timestamp))
	db.commit()

def messageExists(db, messageId):
	if query_db(db, "SELECT messageId FROM messages WHERE messageId = ?", (messageId,)):
		return True
	return False

def markMessage(db, messageId, read):
	db.cursor().execute("UPDATE messages SET read = ? WHERE messageId = ?", (read, messageId))
	db.commit()

# Post Methods
def insertPost(db, postId, timestamp):
	db.cursor().execute("INSERT INTO posts VALUES (?, ?)", (postId, timestamp))
	db.commit()

def postExists(db, postId):
	if query_db(db, "SELECT postId FROM posts WHERE postId = ?", (postId,)):
		return True
	return False

# Comment Methods
