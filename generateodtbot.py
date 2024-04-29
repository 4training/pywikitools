#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Bot that is generating translated odt files:
    - calls translateodt.py (which does the actual work)
    - calls dropboxupload.py for uploading the result to the dropbox
    - sends notification to the mediawiki user who requested the action together with log output (only warning level)
    - sends notification to admin with log output (both warning and debug level)
"""
import argparse
from typing import List
import pywikibot
from os.path import abspath, dirname, join
import sys
import logging
import traceback
import io
from pywikitools.family import Family
from pywikitools.translateodt import TranslateODT
import dropboxupload
import fcntl
import time
from configparser import ConfigParser

CONNECT_TRIES = 10
LOCKFILENAME = 'generateodtbot.lock'    # in the "base" directory as defined in config.ini


class GenerateODTBot:
    def __init__(self, config: ConfigParser):
        # Set up logging: Also catch logs from pywikitools.translateodt, pywikitools.correctbot
        self.logger = logging.getLogger('pywikitools')
        self.logger.setLevel(logging.DEBUG)
        fformatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
        log_path = config.get('Paths', 'logs', fallback='')
        if log_path == '':
            self.logger.warning('No log directory specified in configuration. Using current working directory')
        if config.has_option('generateodtbot', 'logfile'):
            fh = logging.FileHandler(f"{log_path}{config['generateodtbot']['logfile']}")
            fh.setLevel(logging.WARNING)
            fh.setFormatter(fformatter)
            self.logger.addHandler(fh)
        if config.has_option('generateodtbot', 'debuglogfile'):
            fh_debug = logging.FileHandler(f"{log_path}{config['generateodtbot']['debuglogfile']}")
            fh_debug.setLevel(logging.DEBUG)
            fh_debug.setFormatter(fformatter)
            self.logger.addHandler(fh_debug)

        sformatter = logging.Formatter('%(levelname)s: %(message)s')
        self.stream = io.StringIO()
        sh = logging.StreamHandler(self.stream)
        sh.setLevel(logging.WARNING)
        sh.setFormatter(sformatter)
        self.logger.addHandler(sh)
        self.stream_debug = io.StringIO()
        sh_debug = logging.StreamHandler(self.stream_debug)
        sh_debug.setLevel(logging.DEBUG)
        sh_debug.setFormatter(fformatter)
        self.logger.addHandler(sh_debug)

    def notify_user(self, username: str, worksheet: str, languagecode: str, admin: bool):
        user = pywikibot.User(self.site, username)
        if user.isEmailable():
            self.logger.info(f"Sending email to {username}")
            msg = f"Hello {username},\n"
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
            log = self.stream.getvalue()
            if log != "":
                msg += "Please check the following log for any warnings:\n" + log
            else:
                msg += "Everything went smooth, no warnings or remarks :)"
            if admin:
                msg += "\nDEBUG:\n" + self.stream_debug.getvalue()

            ret = user.send_email(f'Generate ODT {worksheet}/{languagecode}', msg)
            if not ret:
                self.logger.error(f"Couldn't send email to user {username}")
        else:
            self.logger.error(f'User {username} is not emailable. No notification sent.')

    def run(self, worksheet: str, languagecode: str, username: str):
        self.logger.debug(f"worksheet: {worksheet}, languagecode: {languagecode}, username: {username}")
        # We use an exclusive lock here because I'm afraid there could be race conditions if two scripts access
        # LibreOffice at the same time
        # So better safe than sorry: We use an exclusive lock here while the script is connecting with LibreOffice
        base_path = config.get('Paths', 'base', fallback='')
        if base_path == '':
            self.logger.warning('No base directory specified in configuration. Using current working directory')
        f = open(f"{base_path}{LOCKFILENAME}", 'w')
        retries = 0
        got_lock = False
        while not got_lock:
            try:
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                retries += 1
                self.logger.debug(f"Couldn't get exclusive lock. Waiting 5s and trying again. Attempt #{retries}")
                if retries > CONNECT_TRIES:
                    self.logger.error(f"Couldn't get exclusive lock. Tried {CONNECT_TRIES} times, giving up.")
                    sys.exit(1)
                time.sleep(5)
            else:
                got_lock = True
        self.logger.info(f"Got exclusive lock. Retries: {retries}")

        try:
            translateodt = TranslateODT()
            filename = translateodt.translate_worksheet(worksheet, languagecode)

            fcntl.flock(f, fcntl.LOCK_UN)       # We can release the lock now
            if isinstance(filename, str):
                if not dropboxupload.upload_file(languagecode, filename):
                    self.logger.error(f"Dropbox upload of {filename} failed!")
                if not dropboxupload.upload_file(languagecode, filename.replace('.odt', '.pdf')):
                    self.logger.error(f"Dropbox upload of {filename.replace('odt', '.pdf')} failed!")
            else:
                self.logger.error("Translateodt failed. See log above or ask an administrator for help.")
            if not dropboxupload.upload_string(languagecode, f'log/{worksheet}.txt', self.stream.getvalue()):
                self.logger.error(f'Dropbox upload of log/{worksheet}.txt failed')
            if not dropboxupload.upload_string(languagecode, f'log/{worksheet}.debug.txt',
                                               self.stream_debug.getvalue()):
                self.logger.error(f'Dropbox upload of log/{worksheet}.debug.txt failed')

            if not config.has_option('generateodtbot', 'site') or \
               not config.has_option('generateodtbot', 'username'):
                self.logger.error("Missing connection settings for generateodtbot in config.ini. "
                                  "Sending no notifications")
                return

            code = config.get('generateodtbot', 'site')
            family = Family()
            self.site = pywikibot.Site(code=code, fam=family, user=config.get('generateodtbot', 'username'))

            # Trying to log in - otherwise notify_user() will fail and raise error
            if not self.site.logged_in():
                self.logger.info("We're not logged in. Trying to log in...")
                self.site.login()

            if self.site.logged_in():
                self.notify_user(username, worksheet, languagecode, False)
                if config.has_option('generateodtbot', 'admin'):
                    self.notify_user(config['generateodtbot']['admin'], worksheet, languagecode, True)
                else:
                    self.logger.warning('No admin in configuration defined. Sending no admin notification')
            else:
                self.logger.error("Couldn't log in. No notifications sent.")

        except Exception as e:
            self.logger.error('Critical error during execution: ' + str(e))
            self.logger.error(traceback.format_exc())


if __name__ == '__main__':
    config = ConfigParser()
    config.read(join(dirname(abspath(__file__)), 'config.ini'))

    log_levels: List[str] = ['debug', 'info', 'warning', 'error']

    desc = 'Generate translated ODT file, make it available and send notifications'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("worksheet", help="Name of the worksheet to translate.")
    parser.add_argument("language_code", help="Target language code for translation.")
    parser.add_argument("username", help="username to send notification after we're finished")
    parser.add_argument("-l", "--loglevel", choices=log_levels, default="warning", help="set loglevel for the script")
    args = parser.parse_args()

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    stdout = logging.StreamHandler(sys.stdout)
    fformatter = logging.Formatter('%(levelname)s: %(message)s')
    stdout.setFormatter(fformatter)
    numeric_level = getattr(logging, args.loglevel.upper(), None)
    assert isinstance(numeric_level, int)
    stdout.setLevel(numeric_level)
    root.addHandler(stdout)

    bot = GenerateODTBot(config)
    bot.run(args.worksheet, args.language_code, args.username)
