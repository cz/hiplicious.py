#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import base64
import datetime
import json
import re
import urllib
import urllib2

config = {
    'DELICIOUS_USERNAME': '-------',
    'DELICIOUS_PASSWORD': '-------',
    'DELICIOUS_BASE_URI': 'https://api.delicious.com/v1',
    'DELICIOUS_SHARED': 'no',
    'HIPCHAT_TOKEN': '-------',
    'HIPCHAT_ROOM': '-------',
    'HIPCHAT_BASE_URI': 'https://api.hipchat.com/v1',
    'HIPCHAT_INCLUDE_FILES': False,
    'LOG_FILE': 'hiplicious.log'
}

# Set up and parse command line argments
parser = argparse.ArgumentParser(description='Import links from a HipChat room\
                                 to Delicious.com')
parser.add_argument('-a', '--all',
                    action='store_true',
                    help='Import the entire history')
parser.add_argument('-c', '--continuous',
                    action='store_true',
                    help='Continue from the specified date until today')
parser.add_argument('-d', '--date',
                    help='Specify a date (YYYY-MM-DD format) to import')
args = parser.parse_args()

def build_url(provider, endpoint, **kwargs):
    """Builds a request URL
    
    :param provider: either 'hipchat' or 'delicious'
    :param endpoint: the API endpoint
    :param **kwargs: optional URL parameters
    """
    if provider == 'hipchat':
        base = config.get('HIPCHAT_BASE_URI')
    elif provider == 'delicious':
        base = config.get('DELICIOUS_BASE_URI')

    # Keep urlencode from choking on unicode data
    # http://stackoverflow.com/a/3121311
    string_kwargs = {}
    for k, v in kwargs.iteritems():
        string_kwargs[k] = unicode(v).encode('utf-8')

    return ''.join([base, endpoint, '?', urllib.urlencode(string_kwargs)])

def make_request(url, auth=None, json_format=True):
    """
    Makes a request using urllib2 and returns the response in the requested
    format.

    :param url: the url to send a request to
    :param auth: (optional) List containing a username and password
    :param json_format: (optional) whether to load the response as json and
        return a Dict. Defaults to True.
    """
    request = urllib2.Request(url)

    if auth and len(auth) == 2:
        base64string = base64.encodestring(':'.join(auth)).replace('\n', '')
        request.add_header("Authorization", "Basic %s" % base64string)

    try:
        response = urllib2.urlopen(request)
    except urllib2.URLError as e:
        print e.reason

    data = response.read()

    if json_format:
        return json.loads(data)
    else:
        return data

def hipchat_get_creation_date():
    """
    Returns the creation date of config['HIPCHAT_ROOM'] in YYYY-MM-DD format
    """

    endpoint = '/rooms/show'
    options = {
        'room_id': config.get('HIPCHAT_ROOM'),
        'format': json,
        'auth_token': config.get('HIPCHAT_TOKEN')
    }
    request_url = build_url('hipchat', endpoint, **options)
    response = make_request(request_url)

    date = datetime.datetime.fromtimestamp(int(response['room']['created']))
    return date.strftime("%Y-%m-%d")

def hipchat_get_log(date):
    """
    Given a date, returns Hipchat log for that date

    :param date: date in YYYY-MM-DD format
    """
    print 'Retrieving log for ', date

    endpoint = '/rooms/history'
    options = {
        'room_id': config.get('HIPCHAT_ROOM'),
        'date': date,
        'format': json,
        'auth_token': config.get('HIPCHAT_TOKEN')
    }
    request_url = build_url('hipchat', endpoint, **options)
    response = make_request(request_url)

    print 'Log retrieved'
    return response

def get_urls_from_log(log, include_files=config.get('HIPCHAT_INCLUDE_FILES',
                                                    False)):
    """
    Given a dict containing a list of Hipchat messages, extracts URLs and builds
    bookmark dicts

    :param log: Dict containing a Hipchat history
    :param include_files: (optional) whether to include file attachment URLs or
        just in-message URLs. Defaults to False.
    """
    print 'Extracting URLs'
    regexp = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F]'\
             '[0-9a-fA-F]))+'
    bookmarks = []

    for item in log['messages']:
        urls = re.findall(regexp, item['message'])
        if urls:
            for url in urls:
                # Remove the URL from the comment itself
                pattern = re.escape(url)
                placeholder = '[link]'
                comment = re.sub(pattern, placeholder, item['message'])

                # Remove characters that choke Delicious's API. Couldn't figure
                # out how to combine these...
                comment = re.sub(u'\u2026', ' ', comment)
                comment = re.sub('[<>]', ' ', comment)

                if comment.strip() == placeholder:
                    comment = ''
                bookmark = {
                    'url': url,
                    'comment': comment,
                    'dt': item['date'],
                    'tags': ','.join([item['from']['name'], 
                                      get_tags_from_message(item['message'])])
                }
                bookmarks.append(bookmark)
        if include_files:
            if item.get('file'):
                bookmark = {
                    'url': item['file']['url'],
                    'comment': comment,
                    'dt': item['date'],
                    'tags': ','.join([item['from']['name'], 'file',
                                      get_tags_from_message(item['message'])])
                }
                bookmarks.append(bookmark)
    print len(bookmarks), ' bookmarks found'
    return bookmarks

def get_tags_from_message(message):
    """
    Given a message string, extracts hashtags and returns a comma-separated list

    :param message: a Hipchat message body
    """
    tags = {word.strip('#') for word in message.split() if word.startswith('#')}
    return ','.join(tags)

def format_date_string(datestring):
    """
    Given a Hipchat-style date string, reformat to Delicious-style date string,
    e.g. 2013-08-06T19:46:49+0000 to 2013-08-06T19:46:49Z

    :param datestring: the Hipchat date string
    """
    return re.sub('\+(.)*$', 'Z', datestring)

def delicious_add_bookmarks(bookmarks):
    print 'Adding bookmarks to delicious.com'

    endpoint = '/posts/add'

    for bookmark in bookmarks:
        #print bookmark.get('comment')
        options = {
            'url': bookmark.get('url'),
            'description': bookmark.get('url'),
            'extended': bookmark.get('comment'),
            'tags': bookmark.get('tags'),
            'dt': format_date_string(bookmark.get('dt')),
            'shared': config.get('DELICIOUS_SHARED')
        }
        request_url = build_url('delicious', endpoint, **options)
        creds = [config.get('DELICIOUS_USERNAME'),
                 config.get('DELICIOUS_PASSWORD')]
        response = make_request(request_url, auth=creds, json_format=False)

        if 'done' in response:
           print ' '.join(['Added', bookmark.get('url')])
        else:
            print ' '.join(['Could not add', bookmark.get('url')])
            with open(config.get('LOG_FILE'), 'a') as logfile:
                logfile.write('\n' + bookmark.get('url'))

def make_my_hipchat_delicious(start, continuous=False):
    """Iterates over dates and runs the import/export
    
    :param start: String of a start date in YYYY-MM-DD format.
    :param continuous: (optional) whether to proceed from the start date until
        today. Defaults to False. 
    """

    if continuous:
        date = datetime.datetime.strptime(start, '%Y-%m-%d').date()
        while date <= datetime.date.today():
            run_import(date.strftime('%Y-%m-%d'))
            date += datetime.timedelta(days=1)
    else:
        run_import(start)

def run_import(date):
    """Runs the import steps
    
    :param date: Date in YYYY-MM-DD format
    """
    log = hipchat_get_log(date)
    bookmarks = get_urls_from_log(log)
    delicious_add_bookmarks(bookmarks)

if __name__ == '__main__':
    if args.date:
        desired_date = args.date
    elif args.all:
        desired_date = hipchat_get_creation_date()
    else:
        desired_date = datetime.date.today().strftime('%Y-%m-%d')

    continuous = args.continuous

    make_my_hipchat_delicious(desired_date, continuous)