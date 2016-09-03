import praw
import time
import traceback

import Config

try:
	import Config
	REDDITUSERNAME     = Config.redditUsername
	REDDITPASSWORD     = Config.redditPassword
	REDDITUSERAGENT    = Config.redditUserAgent
	REDDITAPPID        = Config.redditAppId
	REDDITAPPSECRET    = Config.redditAppSecret
	REDDITREFRESHTOKEN = Config.redditRefreshToken
	GOODREADSKEY       = Config.goodreadsKey
	GOODREADSSECRET    = Config.goodreadsSecret
except ImportError:
	print "import error"

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

def mainLoop():
	print "Starting main loop"
	comment_stream = praw.helpers.comment_stream(reddit, 'taptitanstest', limit=2)
	for comment in comment_stream:
		print comment.body

setupReddit()

while 1:
	try:
		mainLoop()
	except Exception as e:
		traceback.print_exc()