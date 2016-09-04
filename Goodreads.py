import requests
import xmltodict
import traceback
import pprint
import json

import Config

pp = pprint.PrettyPrinter(indent=2)

GOODREADSKEY       = Config.goodreadsKey
GOODREADSSECRET    = Config.goodreadsSecret

def addApiKey(r):
	if "?" in r:
		return r + "&key=" + GOODREADSKEY
	return r + "?key=" + GOODREADSKEY

def makeRequest(r):
	return requests.get(addApiKey(r))

def parseResponse(response):
	try:
		return xmltodict.parse(response.content)
	except Exception as e:
		traceback.print_exc()

def searchForBook(title, author = None):
	apiUrl = 'https://www.goodreads.com/search/index.xml?q={0}'
	r = makeRequest(apiUrl.format(title))
	searchResults = parseResponse(r)

	results = searchResults["GoodreadsResponse"]["search"]["results"]["work"]
	bookId = int(results[0]["best_book"]["id"]["#text"])
	bookAuthorId = int(results[0]["best_book"]["author"]["id"]["#text"])

	averageRating = float(results[0]["average_rating"])
	bookTitle = str(results[0]["best_book"]["title"])
	bookAuthor = str(results[0]["best_book"]["author"]["name"])

	# print type(averageRating), averageRating
	# print type(bookId), bookId
	# print type(bookTitle), bookTitle
	# print type(bookAuthor), bookAuthor
	# print type(bookAuthorId), bookAuthorId

	# print book_data["GoodreadsResponse"]["search"]["results"]

	# print "got info"
	# print json.dumps(book_data, indent=2)
	# pp.pprint(book_data)

	return bookId, bookAuthorId

def getBookInformation(bid):
	apiUrl = 'https://www.goodreads.com/book/show/{0}?format=xml'
	r = makeRequest(apiUrl.format(bid))
	bookInfo = parseResponse(r)
	# print json.dumps(bookInfo, indent=2)

	book = bookInfo["GoodreadsResponse"]["book"]

	return {
		"bookId": book["id"],
		"bookTitle": book["title"],
		"bookISBN": book["isbn"],
		"bookPublisherYear": book["publication_year"],
		"bookPublisherMonth": book["publication_month"],
		"bookPublisherDay": book["publication_day"],
		"bookPublisher": book["publisher"],
		"bookDescription": book["description"],
		"bookReviewsNum": book["work"]["reviews_count"]["#text"],
		"bookRatingsNum": book["ratings_count"],
		"bookRatingsDist": book["work"]["rating_dist"],
		"bookAverageRating": book["average_rating"]
	}

def getBookUrlFromId(bid):
	return 'https://www.goodreads.com/book/show/{0}'.format(bid)

def getAuthorInformation(aid):
	apiUrl = 'https://www.goodreads.com/author/show/{0}?format=xml'
	r = makeRequest(apiUrl.format(aid))
	authorInfo = parseResponse(r)

	author = authorInfo["GoodreadsResponse"]["author"]

	return {
		"authorName": author["name"],
		"authorFans": author["fans_count"]["#text"],
		"authorDescription": author["about"],
		"authorDOB": author["born_at"]
	}

def getAuthorUrlFromId(aid):
	return 'https://www.goodreads.com/author/show/{0}'.format(bid)

# searchForBook("Ender's Game", None)

# getBookInformation(375802)
# getAuthorInformation(589)

#     r = requests.get(api_url.format(goodreads_id, goodreads_api_key))

# https://www.goodreads.com/search/index.xml?key=FNiCaGXEW4EazsE9lSvw&q=Ender%27s+Game