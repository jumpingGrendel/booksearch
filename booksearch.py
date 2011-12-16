import base64, hashlib, hmac, time
from urllib import urlencode, quote_plus
import HTMLParser
from StringIO import StringIO
import string
from lxml import etree
from lxml import objectify
from pdb import set_trace
import ConfigParser
import sys

config = ConfigParser.ConfigParser()
config.read("config.ini")

AWS_ACCESS_KEY_ID = config.get("myvars", 'AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = config.get("myvars", 'AWS_SECRET_ACCESS_KEY')
AWS_ASSOCIATE_TAG = config.get("myvars", 'AWS_ASSOCIATE_TAG')

def getSignedUrl(title,author):
    base_url = "http://ecs.amazonaws.com/onca/xml"
    url_params = dict(
        Service='AWSECommerceService', 
        Operation='ItemSearch', 
        IdType='ISBN', 
        Title=quote_plus(title),
        Author=quote_plus(author),
        SearchIndex='Books',
        IncludeReviewsSummary=False,
        AWSAccessKeyId=AWS_ACCESS_KEY_ID,
        AssociateTag=AWS_ASSOCIATE_TAG,
        ResponseGroup='ItemAttributes,Images')

    url_params['Timestamp'] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # Sort the URL parameters by key
    keys = url_params.keys()
    keys.sort()
    # Get the values in the same order of the sorted keys
    values = map(url_params.get, keys)

    # Reconstruct the URL parameters and encode them
    url_string = urlencode(zip(keys,values))

    #Construct the string to sign
    string_to_sign = "GET\necs.amazonaws.com\n/onca/xml\n%s" % url_string

    # Sign the request
    signature = hmac.new(
        key=AWS_SECRET_ACCESS_KEY,
        msg=string_to_sign,
        digestmod=hashlib.sha256).digest()

    # Base64 encode the signature
    signature = base64.encodestring(signature).strip()

    # Make the signature URL safe
    urlencoded_signature = quote_plus(signature)
    url_string += "&Signature=%s" % urlencoded_signature

    return "%s?%s" % (base_url, url_string)
    
f = open('top_100_david_pringle.html')
list_html = f.read()
f.close()

parser = etree.HTMLParser()
tree   = etree.parse(StringIO(list_html), parser)
list_elements = tree.xpath('//li')

count=1
for li in list_elements:
    title_author = string.split(li.text, ' - ')
    title = title_author[1]
    author = title_author[0]
    signedUrl = getSignedUrl(title, author)
    print count
    #if count > 5:
    #    break
    print signedUrl
    root = objectify.parse(signedUrl).getroot()
    
    try:
        for item in root.Items.Item:

            if(item.ItemAttributes.Binding != 'Audio Cassette'):
                try:
                    isbn = str(item.ItemAttributes.ISBN)
                    if len(isbn) == 9:
                        isbn = '0%s' % isbn
                    span = etree.SubElement(li,"span")
                    span.set('class', 'isbn')
                    span.text = "(%s)" % isbn
                    href = etree.SubElement(li,"a")
                    href.set('href',str(item.DetailPageURL))
                    href.text = "details"
                    li.text = "%s - %s " % (title_author[0], title_author[1])
#                    set_trace()
                    break
                except AttributeError:
                    # doesn't have an ISBN, use the ASIN
                    print "attribute error %s" % title_author[0]
                    isbn = str(item.ASIN)
                    if len(isbn) == 9:
                        isbn = '0%s' % isbn
                    span = etree.SubElement(li,"span")
                    span.set('class', 'asin')
                    span.text = "(%s)" % isbn
                    href = etree.SubElement(li,"a")
                    href.set('href',str(item.DetailPageURL))
                    href.text = "details"
                    li.text = "%s - %s " % (title_author[0], title_author[1])
#                    set_trace()
                    break
    except AttributeError:
        print AttributeError
    count += 1
    
#write new html doc to file
result = etree.tostring(tree, pretty_print=True, method="html")

fout = open("top100.html", "w")
fout.write(result)
fout.close()
