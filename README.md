# hiplicious.py

Import links and files from a Hipchat room to Delicious.com 

## Usage

1. Open hiplicious.py and update the config with your creds (see below)
2. Run that sh-t

## Examples

Import everything

	python hiplicious.py -a

Import today (put this badboy on a cron)

	python hiplicious.py

Import a specific date

	python hiplicious.py -d 2012-12-21

Import everything from a specific date until today

	python hiplicious.py -c -d 2012-12-21

## Config options

### `DELICIOUS_USERNAME` and `DELICIOUS_PASSWORD`
Pretty self-explanatory

### `DELICIOUS_BASE_URI`
Leave this alone

### `DELICIOUS_SHARED`
`no` to keep bookmarks private, `yes` to make them public

### `HIPCHAT_TOKEN`
Your Hipchat API token. You need an [admin token](https://www.hipchat.com/admin/api).

### `HIPCHAT_ROOM`
For now, hiplicious.py can only do one room. Here's how you find your room's ID:

- [Use the API](https://www.hipchat.com/docs/api/method/rooms/list)
- Log into the Hipchat web app, open the room, click "Room actions", click "Browse chat history," and get the Room ID from the URL

### `HIPCHAT_BASE_URI`
Leave this alone

### `HIPCHAT_INCLUDE_FILES`
Whether to include file attachment URLs. `True` or `False`

## TODO

- Allow room id to be passed on the command line
- Maybe a way to find the room id if passed the room's name
- Better logging
- Become smarter and write better code