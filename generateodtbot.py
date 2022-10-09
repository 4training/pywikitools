#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Bot that is generating translated odt files:
    - calls translateodt.py (which does the actual work)
    - calls dropboxupload.py for uploading the result to the dropbox
    - sends notification to the mediawiki user who requested the action together with log output (only warning level)
    - sends notification to admin with log output (both warning and debug level)
"""
import pywikibot
import getopt
import os
import sys
import logging
import traceback
import io
from pywikitools.translateodt import TranslateODT
import dropboxupload
import fcntl
import time
import configparser

CONNECT_TRIES = 10
LOCKFILENAME = 'generateodtbot.lock'    # in the "base" directory as defined in config.ini

global_site = pywikibot.Site()
# Read the configuration from config.ini in the same directory
config = configparser.ConfigParser()
config.read(os.path.dirname(os.path.abspath(__file__)) + '/config.ini')

logger = logging.getLogger('pywikitools')   # Also catch logs from pywikitools.translateodt and pywikitools.correctbot
logger.setLevel(logging.DEBUG)
fformatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
log_path = config.get('Paths', 'logs', fallback='')
if log_path == '':
    logger.warning('No log directory specified in configuration. Using current working directory')
if config.has_option('generateodtbot', 'logfile'):
    fh = logging.FileHandler(log_path + config['generateodtbot']['logfile'])
    fh.setLevel(logging.WARNING)
    fh.setFormatter(fformatter)
    logger.addHandler(fh)
if config.has_option('generateodtbot', 'debuglogfile'):
    fh_debug = logging.FileHandler(log_path + config['generateodtbot']['debuglogfile'])
    fh_debug.setLevel(logging.DEBUG)
    fh_debug.setFormatter(fformatter)
    logger.addHandler(fh_debug)

sformatter = logging.Formatter('%(levelname)s: %(message)s')
stream = io.StringIO()
sh = logging.StreamHandler(stream)
sh.setLevel(logging.WARNING)
sh.setFormatter(sformatter)
logger.addHandler(sh)
stream_debug = io.StringIO()
sh_debug = logging.StreamHandler(stream_debug)
sh_debug.setLevel(logging.DEBUG)
sh_debug.setFormatter(fformatter)
logger.addHandler(sh_debug)


# Reading command line arguments
def usage():
    print("Usage: python3 pwb.py generateodtbot.py worksheet languagecode username")


def notify_user(username: str, worksheet: str, languagecode: str, admin: bool):
    user = pywikibot.User(global_site, username)
    if user.isEmailable():
        logger.info('Sending email to ' + username)
        msg = "Hello " + username + ",\n"
        msg += """
The automated generation of the translated .odt and .pdf files is finished. You find them in the Dropbox:
https://www.dropbox.com/sh/sghbc73ekwm39r2/AADPw-KftZkwjXUM6e3Xqdtpa?dl=0

Please check the PDF: If everything is fine and it fits well, you can directly upload both files.

Otherwise open the ODT file and adjust the formatting until everything looks nice and fits well.
When you're done, save the file and export a PDF (with the right options).

Upload files here: https://www.4training.net/Special:Upload
Afterwards they will be available for everyone to download and use them easily.
Here you find the detailed documentation for all the steps:
https://www.4training.net/4training:Creating_and_Uploading_Files

Take a moment to think and pray: Who would need that content and you could teach them?
Who could you send this file so that they would benefit from it? Who could you give a printed copy?
Ask us for support if you have any questions on how to teach this worksheet or want more training.

Thank you very much for all your work!


"""
        log = stream.getvalue()
        if log != "":
            msg += "Please check the following log for any warnings:\n" + log
        else:
            msg += "Everything went smooth, no warnings or remarks :)"
        if admin:
            msg += "\nDEBUG:\n" + stream_debug.getvalue()

        ret = user.send_email('Generate ODT ' + worksheet + '/' + languagecode, msg)
        if not ret:
            logger.error("Couldn't send email to user " + username)
    else:
        logger.error('User ' + username + ' is not emailable. No notification sent.')


try:
    opts, args = getopt.getopt(sys.argv[1:], "h", ["help"])
except getopt.GetoptError as err:
    # print help information and exit:
    print(err)
    usage()
    sys.exit(2)
if (len(args) != 3):
    usage()
    sys.exit(2)
worksheet = args[0]
languagecode = args[1]
username = args[2]
for o, a in opts:
    if o in ("-h", "--help"):
        usage()
        sys.exit()
    else:
        logger.warning("Unhandled option: " + o)

logger.debug("worksheet: " + worksheet + ", languagecode: " + languagecode + ", username: " + username)

# We use an exclusive lock here because I'm afraid there could be race conditions if two scripts access
# LibreOffice at the same time
# So better safe than sorry: We use an exclusive lock here for the time the script is connecting with LibreOffice
base_path = config.get('Paths', 'base', fallback='')
if base_path == '':
    logger.warning('No base directory specified in configuration. Using current working directory')
f = open(base_path + LOCKFILENAME, 'w')
retries = 0
got_lock = False
while not got_lock:
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        retries += 1
        logger.debug("Couldn't get exclusive lock. Waiting 5s and trying again. This is attempt #" + str(retries))
        if retries > CONNECT_TRIES:
            logger.error("Couldn't get exclusive lock. Tried " + str(CONNECT_TRIES) + " times, giving up now.")
            sys.exit(1)
        time.sleep(5)
    else:
        got_lock = True
logger.info('Got exclusive lock. Retries: ' + str(retries))

try:
    translateodt = TranslateODT()
    filename = translateodt.translate_worksheet(worksheet, languagecode)

    fcntl.flock(f, fcntl.LOCK_UN)       # We can release the lock now
    if isinstance(filename, str):
        if not dropboxupload.upload_file(languagecode, filename):
            logger.error("Dropbox upload of " + filename + " failed!")
        if not dropboxupload.upload_file(languagecode, filename.replace('.odt', '.pdf')):
            logger.error("Dropbox upload of " + filename.replace('odt', '.pdf') + " failed!")
    else:
        logger.error("Translateodt failed. See log above or ask an administrator for help.")
    if not dropboxupload.upload_string(languagecode, 'log/' + worksheet + '.txt', stream.getvalue()):
        logger.error('Dropbox upload of log/' + worksheet + '.txt failed')
    if not dropboxupload.upload_string(languagecode, 'log/' + worksheet + '.debug.txt', stream_debug.getvalue()):
        logger.error('Dropbox upload of log/' + worksheet + '.debug.txt failed')
    notify_user(username, worksheet, languagecode, False)
    if config.has_option('generateodtbot', 'admin1'):
        notify_user(config['generateodtbot']['admin1'], worksheet, languagecode, True)
    else:
        logger.warning('No admin1 in configuration defined. Sending no admin notification')
    if config.has_option('generateodtbot', 'admin2'):
        notify_user(config['generateodtbot']['admin2'], worksheet, languagecode, True)

except Exception as e:
    logger.error('Critical error during execution: ' + str(e))
    logger.error(traceback.format_exc())
