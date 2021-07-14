from pywikibot import Site, Page
import logging
import sys

Logger = logging.getLogger("ServerCommunicator")


class ServerCommunicator:
    """Communicates directly with 4training.net-server and offers fetching the text of the given address and saving it
    """
    __slots__ = ['__global_site']

    def __init__(self):
        self.__global_site = Site()

    def request_text_from_server(self, address: str) -> str:
        """Requests text content of given address on 4training.net-server

        Args:
            address (str): Address to request text content from

        Returns:
            str: Text content for given address
        """
        try:
            page: Page = Page(self.__global_site, address)
            if not page.exists():
                Logger.fatal("Requested page does not exist")
                sys.exit(1)
            return page.text
        except Exception:
            Logger.fatal("Requested page not reachable")
            sys.exit(1)

    def send_text_to_server(self, address: str, content: str) -> None:
        """Sends text content to given address on 4training.net-server

        Args:
            address (str): Address to send text content to
            content (str): Text content
        """
        try:
            page: Page = Page(self.__global_site, address)
            if not page.exists():
                Logger.fatal("Requested page does not exist")
                sys.exit(1)
            page.text = content
            page.save("Typos fixed by CorrectBot")
        except Exception:
            Logger.fatal("Requested page not reachable")
            sys.exit(1)
