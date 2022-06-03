from github import Github
from launchpadlib.launchpad import Launchpad
import os

# PAT is read from environment variables, this will error if not set
GH_PAT = os.environ['GH_PAT']

launchpad = Launchpad.login_with('stonepreston-github-migration-testing', 'staging', version='devel')
projects = launchpad.projects
project = projects['stonepreston-github-migration-testing']
bug_tasks = project.searchTasks()
bugs = []
for bt in bug_tasks:
    b = launchpad.load(str(bt.bug))
    bugs.append(b)

g = Github(GH_PAT)
repo = g.get_repo("stonepreston/github-issues-to-launchpad-bugs")
issues = repo.get_issues(state="all")
for issue in issues:
    title = issue.title
    # GH issues dont have mandatory descriptions like LP bugs. GH Issues only have comments
    # we could make the desc and the tile the same, since the desc cannot be empty
    description = title
    tags = [x.name for x in issue.labels]
    # GH issues are either opened or closed. LP issues have a myriad of status possibilities
    # for closed issues it might make sense to mark them as triaged since theres no way of knowning
    # if they were fix commited, fix released, wont fix, etc.
    status = 'New' if issue.state == 'open' else 'Triaged'

    # check if the issue already exists
    exists = False
    for b in bugs:
        if b.title == title:
            exists = True
    if exists:
        print(f'Bug {title} already exists, skipping')
        continue

    # Create the bug in launchpad
    print(f'Creating bug {title}')
    bug = launchpad.bugs.createBug(description=description,
                                   tags=tags, information_type='Public',
                                   security_related=False, title=title,
                                   target=project)

    # Update status
    print(f'Updating status to {status}')
    tasks = bug.bug_tasks
    for task in tasks:
        task.status = status
        task.lp_save()

    # Update comments
    print(f'Updating comments')
    for comment in issue.get_comments():
        content = f'{comment.user.login} commented at {comment.created_at}\n{comment.body}'
        bug.newMessage(content=content)

