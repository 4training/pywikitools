#!/usr/bin/python3
"""
CGI handler that receives the request to generate a translated ODT.
This calls the generateodtbot which is doing the actual job
"""

import subprocess
import sys
import configparser
from pathlib import Path

# Import modules for CGI handling
import cgi

if __name__ == '__main__':
    # Create instance of FieldStorage
    form = cgi.FieldStorage()

    # Get data from fields
    page = form.getvalue('worksheet')
    username = form.getvalue('user')

    # TODO return a proper response with correct headers e.g. in json format
    # see https://social.msdn.microsoft.com/Forums/ie/en-US/0f089d43-5f8a-48e6-84d2-e176f3c629b9/correct-answer-to-a-httppost-request
    print("Content-type:text/html\r\n\r\n")
    print('<html><head><meta http-equiv="content-type" content="text/html; charset=utf-8" /><title>Generate ODT</title></head><body>')
    if not isinstance(page, str):
        print("Error: no worksheet argument given.")
        sys.exit(1)
    if not isinstance(username, str):
        print('Error: no username argument given.')
        sys.exit(1)

    slash = page.find('/')
    if slash:
        worksheet = page[0:slash]
        languagecode = page[slash+1:]
    else:
        print(F"Error: invalid worksheet argument: {page}")
        sys.exit(1)

    # Read the configuration from config.ini in the parent directory
    config = configparser.ConfigParser()
    path = Path(__file__)
    config.read(str(path.resolve().parent.parent) + '/config.ini')
    if config.has_option('Paths', 'pwb') and config.has_option('Paths', 'generateodtbot'):
        args = [config['Paths']['pwb'], config['Paths']['generateodtbot'],
                worksheet, languagecode, username]
        if config.has_option('Paths', 'python'):
            args.insert(0, config['Paths']['python'])
        if config.has_option('generateodtbot', 'sudouser'):
            args = ['sudo', '-u', config['generateodtbot']['sudouser']] + args
        script = subprocess.Popen(args)
        exit_code = script.wait()
        if exit_code == 0:
            print('Success')
        else:
            # TODO give a more informative error message
            print('Error: Please ask an administrator for help')
    else:
        print('Error: Configuration missing or incomplete. Aborting.')
    print('</body></html>')
