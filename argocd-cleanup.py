#!/usr/bin/python3

# pip install git-python sh pyyaml

from git import Repo
import os
import re
import sh
import yaml


class ArgocdCleanup:
    REMOTE_NAME = 'origin'

    def __init__(self):
        """ This constructor loads configuration information from a yaml file
            and initializes internal variables.
        """
        self.argocd_server = os.environ['ARGOCD_SERVER']
        self.argocd_username = os.environ['ARGOCD_USERNAME']
        self.argocd_password = os.environ['ARGOCD_PASSWORD']
        self.argocd_configfile = os.environ['CONFIG_FILE']
        print("* Loading configuration...", flush=True)
        config = self.load_configuration()
        self.config_repo_mapping = config['configuration']['repo_mapping']
        self.main_branch = config['configuration']['main_branch']
        self.log_only = config['configuration']['log_only']
        self.delete_merged_branches = config['configuration']['delete_merged_branches']
        self.branches_to_delete = []
        self.apps_to_delete = []
        print("  Done")

    def cleanup_argocd_applications(self):
        """ Logs into ArgoCD and analyzes DEV applications

            * If the remote branch no longer exists, the application is deleted
            * If the remote branch exists but was merged to main, the application is deleted
              * Optionally the remote branch can be deleted as well
        """
        print("* Logging in to Argocd...", flush=True)
        self.argocd_login()
        print("  Done")

        print("* Retrieving Application Information...", flush=True)
        application_info = self.argocd_get_app_info()
        print("  Done")

        print("* Analyzing DEV applications", flush=True)
        for application in application_info:
            argocd_app_name = application["metadata"]["name"]
            target_revision = application["spec"]["source"]["targetRevision"]
            if target_revision.endswith("DEV"):
                print("   .", end="", flush=True)
                repo_url = application["spec"]["source"]["repoURL"]
                repo_remote_url = self.get_code_repo_remote(repo_url)
                branch_name = re.search(
                    "-([A-Za-z0-9-]*)", target_revision).group(1)

                repo = self.init_code_repo(repo_remote_url)
                remote = self.create_code_remote(repo, repo_remote_url)

                if not self.branch_exists(branch_name, remote):
                    self.delete_argocd_app(argocd_app_name)
                    self.apps_to_delete.append(argocd_app_name)
                else:
                    self.delete_merged_branch_and_app(
                        branch_name, argocd_app_name, repo, remote)

        print("  Done")
        if (self.log_only):
            print("\n** The following ArgoCD applications would have been deleted")
        else:
            print("\n** The following ArgoCD applications were deleted")
        print(*self.apps_to_delete, sep='\n')

        if (self.log_only or not self.delete_merged_branches):
            print("\n** The following branches would have been deleted")
        else:
            print("\n** The following branches were deleted")
        print(*self.branches_to_delete, sep='\n')

        self.reset()

    def load_configuration(self):
        """ Load configuration data from yaml file

        Returns:
            dict: Configuration information
        """
        with open(self.argocd_configfile, 'r') as config_file:
            config = yaml.safe_load(config_file)
        return config

    def argocd_login(self):
        """ Login to ArgoCD
        """
        sh.argocd("login", self.argocd_server,
                  "--insecure",
                  "--username", self.argocd_username,
                  "--password", self.argocd_password)

    def argocd_get_app_info(self):
        """ Retrieves application information from ArgoCD as yaml

        Returns:
            dict: Application information
        """
        buf = sh.argocd("--insecure", "app", "list", "-o", "yaml")
        return yaml.safe_load(buf.__str__())

    def get_code_repo_remote(self, repo_url):
        """ Retrieves the code git repo remote url corresponding to
            the input config repo url. Adds git credentials if 
            they are defined

        Args:
            repo_url (_type_): _description_

        Returns:
            _type_: _description_
        """
        remote = None
        for entry in self.config_repo_mapping:
            if entry['config_repo'] in repo_url:
                remote = entry['code_remote']
                try:
                    remote_creds = os.environ[entry.get(
                        'remote_creds_env_var')]
                    remote = remote.replace(
                        'https://', f'https://{remote_creds}@')
                except:
                    pass
        return remote

    def create_code_remote(self, repo, repo_remote_url):
        """ Creates local remote for code repo if it does not exist

        Args:
            repo: Local git repository object
            repo_remote_url: git remote url

        Returns:
            _type_: _description_
        """
        remote = None
        try:
            remote = repo.remote(self.REMOTE_NAME)
        except:
            remote = repo.create_remote(self.REMOTE_NAME, repo_remote_url)

        if not remote.exists():
            print(
                f"\nError - unable to verify existence of remote repo for {repo_remote_url}")
        else:
            remote.fetch()
        return remote

    def branch_exists(self, branch_name, remote):
        """ Checks whether the code branch exists in the remote repository

        Args:
            branch_name: Name of the branch to check
            remote: git remote to check for the branch

        Returns:
            boolean: True if the branch exists in the remote, False otherwise
        """
        exists = False
        for remote_ref in remote.refs:
            ref_string_for_matching = remote_ref.__str__().replace('/', '-')
            if ref_string_for_matching.endswith(branch_name):
                exists = True
                break
        return exists

    def init_code_repo(self, repo_remote_url):
        """ Initializzes the code repo

        Args:
            repo_remote_url: url for the git remote

        Returns:
            Initialized remote object
        """
        repo_short_name = re.search(
            ".*/(.*)\.git", repo_remote_url).group(1)
        local_repo_path = os.path.join('/tmp', repo_short_name)
        return Repo.init(local_repo_path)

    def delete_argocd_app(self, name):
        """ Deletes the named argocd application

        Args:
            name: Name of the application to delete
        """
        if not self.log_only:
            print(f"TODO: Deleting argocd app {name}")

    def delete_branch(self, repo, branch):
        """ Delete branch

        Args:
            repo: Repository to delete branch from
            branch: Branch to delete
        """
        if not self.log_only and self.delete_merged_branches:
            print(f"TODO: Deleting {branch} from {repo}")

    def delete_merged_branch_and_app(self, branch_name, argocd_app_name, repo, remote):
        """ If the branch was merged, delete it and the corresponding application in ArgoCD

        Args:
            branch_name (_type_): Name of the branch to delete
            argocd_app_name (_type_): ArgoCD application name
            repo (_type_): git repository
            remote (_type_): git remote
        """
        remote.pull(self.main_branch)
        repo.git.checkout(self.main_branch)
        merged_branches = repo.git.branch(
            '-r', '--merged', self.main_branch).split('\n')
        for branch in merged_branches:
            if f"{self.REMOTE_NAME}-{branch_name}" == branch.strip().replace('/', '-'):
                self.apps_to_delete.append(argocd_app_name)
                self.delete_argocd_app(argocd_app_name)

                self.branches_to_delete.append(branch.strip())
                self.delete_branch(repo, branch.strip())
                break

    def reset(self):
        """ Reset the state of this object
        """
        self.branches_to_delete = []
        self.apps_to_delete = []


if __name__ == "__main__":
    argo_cleaner = ArgocdCleanup()
    argo_cleaner.cleanup_argocd_applications()
