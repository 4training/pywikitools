""" 
Upload created files to a shared Dropbox folder

Dropbox account credentials are stored in a separate file
"""
import sys
import os
import logging
import getopt
import dropbox
from dropbox.files import WriteMode
from dropbox.exceptions import ApiError, AuthError
import configparser

logger = logging.getLogger('4training.dropboxupload')
config = configparser.ConfigParser()
config.read(os.path.dirname(os.path.abspath(__file__)) + '/config.ini')

############################################################################################
# Check inputs
############################################################################################
def usage():
    print("Usage: python3 dropboxupload.py [-l loglevel] languagecode filename")

def _upload(filename: str, content: bytes) -> bool:
    """
    Internal upload function: write content to the specified file
    """
    if (not config.has_option('Dropbox', 'folder')) or (not config.has_option('Dropbox', 'token')):
        logger.error("Dropbox configuration missing or incomplete. Not doing anything.")
        return False

    dbx = dropbox.Dropbox(config['Dropbox'].get('token'))
    # Check that the access token is valid
    try:
        dbx.users_get_current_account()
    except AuthError:
        logger.error("ERROR: Invalid access token; try re-generating an access token from the app console on the web.")
        return False

    logger.debug("Trying to write to Dropbox file " + filename + " ...")
    try:
        dbx.files_upload(content, config['Dropbox'].get('folder') + filename, mode = WriteMode('overwrite'))
    except ApiError as err:
        # This checks for the specific error where a user doesn't have
        # enough Dropbox space quota to upload this file
        if (err.error.is_path() and
                err.error.get_path().reason.is_insufficient_space()):
            logger.error("ERROR: Cannot back up; insufficient space.")
            return False
        elif err.user_message_text:
            logger.error(err.user_message_text)
            return False
        else:
            logger.error(str(err))
            return False
    logger.debug("Dropbox upload was successful.")
    return True

def upload_string(languagecode: str, filename: str, content: str) -> bool:
    """
    Create a new file in the dropbox (OAuth token in config.ini)
    @param languagecode
    @param filename the name of the file that should be created (can also include a relative path)
    @param content fill the file with this content
    @return True if successful
    """
    return _upload(languagecode + '/' + filename, content.encode())

def upload_file(languagecode: str, filename: str) -> bool:
    """
    Upload the specified file to the dropbox (OAuth token in config.ini)
    @param languagecode
    @param filename can also include a path
    @return True for Success, False if error occured
    """
    with open(filename, 'rb') as f:
        # We use WriteMode=overwrite to make sure that the settings in the file are changed on upload
        pos = filename.rfind('/')   # check if filename contains path as well
        if (pos > -1):
            upload_filename = languagecode + "/" + filename[pos+1:]
        else:
            upload_filename = languagecode + "/" + filename

        logger.info("Uploading " + filename + " to Dropbox as " + upload_filename + " ...")
        return _upload(upload_filename, f.read())
    return True

# Check if the script is run as standalone or called by another script
if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hl:", ["help","loglevel"])
    except getopt.GetoptError as err:
        # print help information and exit:
        print(err)
        usage()
        sys.exit(2)
    if (len(args) != 2):
        usage()
        sys.exit(2)
    languagecode = args[0]      # TODO check the validity of this argument
    filename = args[1]
    for o, a in opts:
        if o == "-l":
            numeric_level = getattr(logging, a.upper(), None)
            if not isinstance(numeric_level, int):
                raise ValueError('Invalid log level: %s' % loglevel)
            logging.basicConfig(level = numeric_level)
            logger.setLevel(numeric_level)
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        else:
            logger.warning("Unhandled option: " + o)
    upload_file(languagecode, filename)

