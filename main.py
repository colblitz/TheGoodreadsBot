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
		reddit.set_oauth_app_info(client_id=REDDITAPPID, client_secret=REDDITAPPSECRET, redirect_uri='http://127.0.0.1:65010/' 'authorize_callback')
		reddit.refresh_access_information(REDDITREFRESHTOKEN)
		print "Reddit successfully set up"
	except Exception as e:
		print "Error setting up Reddit: " + str(e)

# PRAW Comment object
def shouldProcess(comment):
	if Database.commentExists(comment.id):
		return False
	if (comment.author.name == REDDITUSERNAME):
		Database.addComment(comment)
		return False

	# limit subreddits
	# limit users
	return True

def formatDate(bookInfo):
	return bookInfo["bookPublisherMonth"].rjust(2, '0') + "/" + bookInfo["bookPublisherDay"].rjust(2, '0') + "/" + bookInfo["bookPublisherYear"]

def generateReply(bookInfo, authorInfo, withStats = False, withDescription = False):
	reply = ""
	reply += u"[{0}]({1}) by {2}".format(
		bookInfo["bookTitle"],
		Goodreads.getBookUrlFromId(bookInfo["bookId"]),
		authorInfo["authorName"])
	if withStats:
		reply += u"\n\n^(**Published:** {0} || **Rating:** {1} over {2} ratings || **Shelves:** {3})".format(
			formatDate(bookInfo),
			bookInfo["bookAverageRating"],
			"{:,}".format(int(bookInfo["bookRatingsNum"])),
			", ".join(bookInfo["bookShelves"]))
	if withDescription:
		reply += u"\n\n> " + bookInfo["bookDescription"].replace("<br><br>", "\n\n> ")
	return reply

def getInfo(searchText):
	bookId, authorId = Goodreads.searchForBook(searchText)
	bookInfo = Goodreads.getBookInformation(bookId)
	authorInfo = Goodreads.getAuthorInformation(authorId)
	print "got info"
	return (bookInfo, authorInfo)

def processComment(comment):
	print "Processing comment: " + comment.id
	things = []

	# ignores all "code" markup (i.e. anything between backticks)
	comment.body = re.sub(r"\`(?s)(.*?)\`", "", comment.body)

	# Things with stats and descriptions {{{Book Title}}}
	for match in re.finditer("\{{3}([^}]*)\}{3}", comment.body, re.X):
		things.append(getInfo(match.group(1)) + (True, True))

	# remove what we just processed
	comment.body = re.sub(r"\{{3}([^}]*)\}{3}", "", comment.body)

	# Things with stats {{Book Title}}
	for match in re.finditer("\{{2}([^}]*)\}{2}", comment.body, re.X):
		things.append(getInfo(match.group(1)) + (True, False))

	# remove what we just processed
	comment.body = re.sub(r"\{{2}([^}]*)\}{2}", "", comment.body)

	# Basic things {Book Title}
	for match in re.finditer("\{([^}]*)\}", comment.body, re.X):
		things.append(getInfo(match.group(1)))

	# remove what we just processed
	comment.body = re.sub(r"\{([^}]*)\}", "", comment.body)

	if things:
		commentReply = "\n\n---\n\n".join(map(lambda t: generateReply(*t), things))
		try:
			comment.reply(commentReply)
			print "Replied to comment"
		except Exception as e:
			traceback.print_exc()
	else:
		print "Nothing to process"

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