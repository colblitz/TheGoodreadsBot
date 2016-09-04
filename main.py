import praw
import time
import traceback
import re

import Config
import Database
import Goodreads

REDDITUSERNAME     = Config.redditUsername
REDDITPASSWORD     = Config.redditPassword
REDDITUSERAGENT    = Config.redditUserAgent
REDDITAPPID        = Config.redditAppId
REDDITAPPSECRET    = Config.redditAppSecret
REDDITREFRESHTOKEN = Config.redditRefreshToken

reddit = praw.Reddit(user_agent=REDDITUSERNAME)

def setupReddit():
	try:
		print "setting up reddit"
		reddit.set_oauth_app_info(client_id=REDDITAPPID,
															client_secret=REDDITAPPSECRET,
															redirect_uri='http://127.0.0.1:65010/' 'authorize_callback')
		reddit.refresh_access_information(REDDITREFRESHTOKEN)
		print "Reddit successfully set up"
	except Exception as e:
		print "Error setting up Reddit: " + str(e)

# PRAW Comment object
def shouldProcess(comment):
	if Database.commentExists(comment.id):
		return False

	# limit subreddits
	# limit users
	return True

def generateReply(bookInfo, authorInfo):
	return "[{0}]({1}), by {2}".format(bookInfo["bookTitle"], Goodreads.getBookUrlFromId(bookInfo["bookId"]), authorInfo["authorName"])

def processComment(comment):
	#ignores all "code" markup (i.e. anything between backticks)
	comment.body = re.sub(r"\`(?s)(.*?)\`", "", comment.body)

	things = []
	for match in re.finditer("""\{{2}   # two open braces {{
															([^}]*) # everything in between
															\}{2}   # two end braces }} """,
													 comment.body, re.X):
		search = match.group(1)
		bookId, authorId = Goodreads.searchForBook(search)
		bookInfo = Goodreads.getBookInformation(bookId)
		authorInfo = Goodreads.getAuthorInformation(authorId)
		things.append((bookInfo, authorInfo))

	commentReply = ""
	for thing in things:
		commentReply += generateReply(thing[0], thing[1]) + "\n"
	if commentReply != "":
		try:
			comment.reply(commentReply)
			print "Replied to comment"
		except Exception as e:
			traceback.print_exc()

def mainLoop():
	print "Starting main loop"
	comment_stream = praw.helpers.comment_stream(reddit, 'taptitanstest', limit=2)
	for comment in comment_stream:
		if (shouldProcess(comment)):
			Database.addComment(comment)
			processComment(comment)

		# print "----"
		# print comment.id
		# print str(comment.subreddit)
		# print str(comment.author)
		# print "--------------"
		# pp.pprint(vars(comment.author))
		# pp.pprint(vars(comment.subreddit))
		# pp.pprint(vars(comment))
		# print json.dumps(vars(comment), indent = 2, sort_keys=True)
		# print comment.body

setupReddit()

while 1:
	try:
		mainLoop()
	except Exception as e:
		traceback.print_exc()