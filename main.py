import praw
import time
import traceback
import re
import threading
import sys

from datetime import date, timedelta

import config
import Database
import Goodreads

import prawcore

REDDITUSERNAME     = config.redditUsername
REDDITPASSWORD     = config.redditPassword
REDDITUSERAGENT    = config.redditUserAgent
REDDITAPPID        = config.redditAppId
REDDITAPPSECRET    = config.redditAppSecret
REDDITREFRESHTOKEN = config.redditRefreshToken

DATABASE = config.databaseFile

class RedditThread(threading.Thread):
	reddit = None
	db = None

	def tPrint(self, s):
		t = time.strftime("%H:%M:%S", time.gmtime())
		m = u"[{} {:17}] {}\n"
		m = m.format(t, self.getName(), unicode(s)).encode('utf-8')
		sys.stdout.write(m)
		sys.stdout.flush()

	def setupReddit(self):
		try:
			self.tPrint("Setting up reddit")
			reddit = praw.Reddit(client_id=REDDITAPPID,
								 client_secret=REDDITAPPSECRET,
								 username=REDDITUSERNAME,
								 password=REDDITPASSWORD,
								 user_agent=REDDITUSERAGENT,
								 refresh_token=REDDITREFRESHTOKEN)
			self.tPrint("Reddit successfully set up")
			return reddit
		except Exception as e:
			self.tPrint("Error setting up Reddit: " + str(e))

SIGNATURE = '''
---

^^Beep ^^boop, ^^I'm ^^a ^^Goodreads ^^bot! ^^\([Github](https://github.com/colblitz/TheGoodreadsBot)) ^^Please ^^PM ^^colblitz ^^with ^^any ^^questions.
'''

SUBREDDITS_TO_WATCH = ['taptitanstest', 'colblitzbottesting']

def redditUserExists(reddit, user):
	try:
		reddit.redditor(user).fullname
	except prawcore.exceptions.NotFound:
		return False
	except:
		return False
	return True

def formatRedditName(name):
	if name is None or name.strip() == '':
		return ''
	return '/u/{}'.format(name.strip())

class MessageThread(RedditThread):
	def logMessage(self, message):
		self.tPrint(unicode("## M ## {} | {} | {}").format(
			message.id,
			message.author,
			unicode(message.subject)))

	def processMessage(self, message):
		if Database.messageExists(self.db, message.id):
			return
		self.logMessage(message)

		self.tPrint(" - Mark message as read")
		message.mark_read()
		Database.markMessage(self.db, message.id, True)

	def run(self):
		self.reddit = self.setupReddit()
		self.db = Database.get_db(DATABASE)
		while 1:
			self.tPrint("Start of loop")
			try:
				for item in self.reddit.inbox.stream():
					self.processMessage(item)
				# for item in reddit.inbox.unread(limit=None):
				# 	if isinstance(item, praw.models.Message):
				# 		process_message(item)
			except Exception as e:
				self.tPrint("Error: " + str(e))
				traceback.print_exc()
				time.sleep(10)

def formatDate(bookInfo):
	return bookInfo["bookPublisherMonth"].rjust(2, '0') + "/" + \
	       ((bookInfo["bookPublisherDay"].rjust(2, '0') + "/") if bookInfo["bookPublisherDay"] else "") + \
	       bookInfo["bookPublisherYear"]

def generateReply(bookInfo, authorInfo, withStats = False, withDescription = False):
	reply = ""
	reply += u"[{0}]({1}) by [{2}]({3})".format(
		bookInfo["bookTitle"],
		Goodreads.getBookUrlFromId(bookInfo["bookId"]),
		authorInfo["authorName"],
		Goodreads.getAuthorUrlFromId(authorInfo["authorId"]))
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

class CommentThread(RedditThread):
	def logComment(self, comment):
		pass

	def processComment(self, comment):
		print "Processing comment: " + comment.id
		things = []
		originalBody = comment.body

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
			print originalBody
			print things
			commentReply = "\n\n---\n\n".join(map(lambda t: generateReply(*t), things))

			print "-------------------------------------------------"
			print commentReply
			try:
				# comment.reply(commentReply)
				print "Replied to comment"
			except Exception as e:
				traceback.print_exc()
		else:
			print "Nothing to process"


	def run(self):
		self.reddit = self.setupReddit()
		self.db = Database.get_db(DATABASE)
		subreddits = [self.reddit.subreddit(srname) for srname in SUBREDDITS_TO_WATCH]
		streams = [sr.stream.comments(pause_after = -1) for sr in subreddits]
		while True:
			try:
				for stream in streams:
					for comment in stream:
						if comment is None:
							break
						self.processComment(comment)
			except Exception as e:
				self.tPrint("Error iterating through comment streams: " + str(e))
				traceback.print_exc()
				time.sleep(10)


class SubmissionThread(RedditThread):
	def logSubmission(self, submission):
		self.tPrint("## S ## {} | {} | {} | {}".format(
			submission.id,
			int(submission.created_utc),
			submission.author,
			submission.title.encode('utf-8')))

	def processSubmission(self, submission):
		if Database.postExists(self.db, submission.id):
			return
		self.logSubmission(submission)
		Database.insertPost(self.db, submission.id, int(submission.created_utc))

	def run(self):
		self.reddit = self.setupReddit()
		self.db = Database.get_db(DATABASE)
		subreddits = [self.reddit.subreddit(srname) for srname in SUBREDDITS_TO_WATCH]
		streams = [sr.stream.submissions(pause_after = -1) for sr in subreddits]
		while True:
			try:
				for stream in streams:
					for submission in stream:
						if submission is None:
							break
						self.processSubmission(submission)
			except Exception as e:
				self.tPrint("Error iterating through submission streams: " + str(e))
				traceback.print_exc()
				time.sleep(10)

if __name__ == '__main__':
	messageThread = MessageThread(name="MessageThread")
	messageThread.daemon = True
	messageThread.start()
	commentThread = CommentThread(name="CommentThread")
	commentThread.daemon = True
	commentThread.start()
	submissionThread = SubmissionThread(name="SubmissionThread")
	submissionThread.daemon = True
	submissionThread.start()

	while True:
		time.sleep(1)
