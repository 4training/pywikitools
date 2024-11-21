import logging
import os
from configparser import ConfigParser
from typing import Final

from git import Actor, Repo
from git.exc import GitError
import pywikibot

from pywikitools.fortraininglib import ForTrainingLib
from pywikitools.resourcesbot.data_structures import LanguageInfo
from pywikitools.resourcesbot.modules.post_processing import LanguagePostProcessor


class ExportRepository(LanguagePostProcessor):
    """
    Export the HTML files (result of ExportHTML) to a git repository.
    Needs to run after ExportHTML.
    """
    @classmethod
    def help_summary(cls) -> str:
        return "Exports the HTML files into a git repo"

    @classmethod
    def abbreviation(cls) -> str:
        return "repository"

    @classmethod
    def can_be_rewritten(cls) -> bool:
        return False

    def __init__(
        self,
        fortraininglib: ForTrainingLib,
        config: ConfigParser,
        site: pywikibot.site.APISite = None,
    ):
        # TODO Currently we assume that origin is correctly set up in the folder,
        #  and we just need to push

        super().__init__(fortraininglib, config, site)
        self._base_folder: str = self._config.get("Paths", "htmlexport", fallback="")
        self.logger: Final[logging.Logger] = logging.getLogger(
            "pywikitools.resourcesbot.modules.export_repository"
        )
        if self._base_folder == "":
            self.logger.warning(
                "Missing htmlexport path in config.ini. Won't export to repository"
            )
        self._author: Final[Actor] = Actor(
            "ExportRepository", "samuel@holydevelopers.net"
        )

    def run(
        self, language_info: LanguageInfo, _english_info, _changes, _english_changes,
        *, force_rewrite: bool = False
    ):
        """Pushing all changes in the local repository (created by ExportHTML) to the
        remote repository.

        Currently, we're ignoring the change parameter and just check for changes
        in the git repository
        """
        # Make sure we have a valid repository
        if self._base_folder == "":
            return
        folder: str = os.path.join(self._base_folder, language_info.language_code)
        try:
            repo = Repo(folder)
        except GitError:
            self.logger.warning(f"No valid repository found in {folder}, skipping.")
            return
        if "origin" not in repo.remotes:
            self.logger.warning(f"Git remote origin missing in {folder}, skipping.")
            return

        # Staging all changes
        untracked: int = len(repo.untracked_files)
        modified: int = 0
        deleted: int = 0
        if untracked > 0:
            self.logger.warning(f"Adding {untracked} untracked files to the repository")
            repo.index.add(repo.untracked_files)
        for item in repo.index.diff(None):
            if item.change_type == "M":
                self.logger.info(f"{str(item.a_path)} modified: Staging for commit")
                repo.index.add(item.a_path)
                modified += 1
            elif item.change_type == "D":
                self.logger.info(f"{item.a_path} deleted: Staging for commit")
                repo.index.remove(item.a_path)
                deleted += 1
            else:
                self.logger.warning(
                    f"Unsupported change_type {item.change_type} in git diff, ignoring."
                )

        if repo.is_dirty():
            # Commiting and pushing to remote
            commit_message = (
                f"Update: {untracked} new, {modified} modified, {deleted} deleted."
            )
            self.logger.warning(f"Pushing to git repository. {commit_message}")
            # TODO add details to the commit message
            repo.index.commit(f"{commit_message}", author=self._author)
            result = repo.remotes.origin.push()
            self.logger.info(f"Pushed to remote, result: {result[0].summary}")
        else:
            self.logger.info(
                f"ExportRepository {language_info.language_code}: No changes."
            )
