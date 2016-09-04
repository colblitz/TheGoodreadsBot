from pymongo import MongoClient
import traceback

client = MongoClient()
db = client['TheGoodreadsBot']
comments = db.comments
requests = db.requests

# {
# 	_id: commentId,
# 	user: username,
# 	subreddit: string,
# 	hadrequest: boolean
# }

# {
# 	author:
# 	title:
# 	user:
# 	subreddit:
# 	date:
# }

def prawCommentToJSON(comment):
	return {
		"_id": comment.id,
		"author": str(comment.author),
		"subreddit": str(comment.subreddit).lower(),
		"date": comment.created_utc,
		"request": 0
	}

# PRAW object
def addComment(comment):
	try:
		cid = comments.insert_one(prawCommentToJSON(comment))
		return cid
	except Exception as e:
		traceback.print_exc()

def commentExists(commentId):
	try:
		c = comments.find_one({"_id": commentId})
		return c != None
	except Exception as e:
		traceback.print_exc()

def addRequest(author, title, user, subreddit, date):
	pass




# iid = db.comments.insert_one({"blah": "test"}).inserted_id

# print db.comments.find_one({"_id": iid})