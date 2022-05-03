#!/usr/bin/python3

# pip install git-python sh pyyaml

import yaml
import sh
import re
import os
import signal
import time
from git import Repo


class ArgocdCleanup:

    REMOTE_NAME = 'origin'

    def __init__(self):

        signal.signal(signal.SIGTERM, self.handler)
        print("* Loading configuration...", end="", flush=True)
        config = self.load_configuration()
        self.config_repo_mapping = config['configuration']['repo_mapping']
        self.main_branch = config['configuration']['main_branch']
        self.log_only = config['configuration']['log_only']
        self.frequency = config['configuration']['frequency_in_seconds']
        self.delete_merged_branches = config['configuration']['delete_merged_branches']
        self.branches_to_delete = []
        self.apps_to_delete = []
        self.argocd_server = os.environ['ARGOCD_SERVER']
        self.argocd_username = os.environ['ARGOCD_USERNAME']
        self.argocd_password = os.environ['ARGOCD_PASSWORD']
        print("Done")

    def handler(self, signum, frame):
        print("\n\n*** Received SIGTERM - exiting ***")
        exit(0)

    def start(self):
        while True:
            self.analyze_argocd_applications()
            print(f"\n* Waiting {self.frequency} seconds...",
                  end="", flush=True)
            time.sleep(self.frequency)
            print("Done")

    def analyze_argocd_applications(self):
        print("* Logging in to Argocd...", end="", flush=True)
        self.argocd_login()
        print("Done")

        print("* Retrieving Application Information...", end="", flush=True)
        application_info = self.argocd_get_app_info()
        print("Done")

        print("* Analyzing DEV applications", end="", flush=True)
        for application in application_info:
            argocd_app_name = application["metadata"]["name"]
            target_revision = application["spec"]["source"]["targetRevision"]
            if target_revision.endswith("DEV"):
                print(".", end="", flush=True)
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
                    # print(f'Branch "{branch_name}" does not exist in "{repo_short_name}". I should delete the "{argocd_app_name}" application in ArgoCD')
                    self.delete_merged_branch_and_app(
                        branch_name, argocd_app_name, repo)

        print("Done")
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
        with open('config.yaml', 'r') as config_file:
            config = yaml.safe_load(config_file)
        return config

    def argocd_login(self):
        sh.argocd("login", self.argocd_server,
                  "--username", self.argocd_username,
                  "--password", self.argocd_password)

    def argocd_get_app_info(self):
        buf = sh.argocd("app", "list", "-o", "yaml")
        return yaml.safe_load(buf.__str__())

    def get_code_repo_remote(self, repo_url):
        for entry in self.config_repo_mapping:
            if entry['config_repo'] in repo_url:
                return entry['code_remote']

    def create_code_remote(self, repo, repo_remote_url):
        remote = None
        try:
            remote = repo.remote(self.REMOTE_NAME)
        except:
            remote = repo.create_remote(self.REMOTE_NAME, repo_remote_url)

        if not remote.exists():
            print(
                f"\nError - unable to verify existence of remote repo for {repo_remote_url}")
        return remote

    def branch_exists(self, branch_name, remote):
        exists = False
        for remote_ref in remote.refs:
            ref_string_for_matching = remote_ref.__str__().replace('/', '-')
            if ref_string_for_matching.endswith(branch_name):
                exists = True
                break
        return exists

    def init_code_repo(self, repo_remote_url):
        repo_short_name = re.search(
            ".*/(.*)\.git", repo_remote_url).group(1)
        local_repo_path = os.path.join('/tmp', repo_short_name)
        return Repo.init(local_repo_path)

    def delete_argocd_app(self, name):
        if not self.log_only:
            print(f"TODO: Deleting argocd app {name}")

    def delete_branch(self, repo, branch):
        if not self.log_only and self.delete_merged_branches:
            print(f"TODO: Deleting {branch} from {repo}")

    def delete_merged_branch_and_app(self, branch_name, argocd_app_name, repo):
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
        self.branches_to_delete = []
        self.apps_to_delete = []


if __name__ == "__main__":
    argo_cleaner = ArgocdCleanup()
    argo_cleaner.start()
