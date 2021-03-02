from flask import Flask
from flask import request
import json
import requests
import helpers

# Config values
application_host = ''
application_port = ''
application_debug = False
error_color = ''
alert_color = ''
success_color = ''
mattermost_url = ''
mattermost_user = ''
mattermost_icon = ''
bitbucket_url = ''
bitbucket_ignore_comments = False

class Attachment:
    def __init__(self):
        self.author_name = ''
        self.author_icon = ''
        self.author_link = ''
        self.fallback = ''
        self.color = ''
        self.pretext = ''
        self.text = ''
        self.title = ''
        self.fields = []

    def to_dict(self):
        d = self.__dict__
        d['fields'] = [f.__dict__ for f in self.fields]
        return d

class AttachmentField:
    def __init__(self):
        self.short = True
        self.title = ''
        self.value = ''

class User:
    def __init__(self):
        self.name = ''
        self.display_name = ''
        self.email = ''
        self.url = ''
        self.avatar = ''

    @classmethod
    def from_bb_data(cls, data_user):
        u = User()
        u.name = data_user["name"]
        u.display_name = data_user["displayName"]
        u.email = data_user["emailAddress"]
        u.url = data_user["links"]["self"][0]["href"]
        u.avatar = u.url + "/avatar.png"
        return u

class Repository:
    def __init__(self):
        self.project = ''
        self.slug = ''
        self.name = ''
        self.url = ''

    @classmethod
    def from_bb_data(cls, repo_data):
        r = Repository()
        r.project = Project.from_bb_data(repo_data["project"])
        r.name = repo_data["name"]
        r.slug = repo_data["slug"]
        r.url = repo_data["links"]["self"][0]["href"]
        return r

class Comment:
    def __init__(self):
        self.id = ''
        self.commit = ''
        self.author = User()
        self.text = ''
        self.content_raw = ''
        self.content_html = ''
        self.content_markup = ''
        self.repository = None

    @classmethod
    def from_bb_data(cls, data):
        c = Comment()
        comment_data = data["comment"]
        c.id = comment_data["id"]
        c.text = comment_data["text"]
        c.commit = data.get("commit")
        c.author = User.from_bb_data(comment_data["author"])
        content = comment_data.get("comments")
        if content is not None and len(content) > 0:
            c.content_raw = content.get("raw", "")
            c.content_html = content.get("html", "")
            c.content_markup = content.get("markup", "")
        if data.get("repository") is not None:
            c.repository = Repository.from_bb_data(data["repository"])
        return c

class Project:
    def __init__(self):
        self.key = ''
        self.name = ''
        self.url = ''

    @classmethod
    def from_bb_data(cls, proj_data):
        p = Project()
        p.key = proj_data["key"]
        p.name = proj_data["name"]
        p.url = proj_data["links"]["self"][0]["href"]
        return p

class Ref:
    def __init__(self):
        self.id = ''
        self.display_id = ''
        self.latest_commit = ''
        self.latest_commit_url = ''
        self.repository = Repository()
        self.url = ''

    @classmethod
    def from_bb_data(cls, ref_data):
        r = Ref()
        r.id = ref_data["id"]
        r.display_id = ref_data["displayId"]
        r.latest_commit = ref_data["latestCommit"]
        r.latest_commit_url = "/commits?until=" + r.id
        r.repository = Repository.from_bb_data(ref_data["repository"])
        r.url = "/commits/" + r.latest_commit

        return r

class RefChange:
    def __init__(self):
        self.id = ''
        self.display_id = ''
        self.from_hash = ''
        self.to_hash = ''
        self.type = ''

    @classmethod
    def from_bb_data(cls, refchange_data):
        rc = RefChange()
        rc.id = refchange_data["ref"]["id"]
        rc.display_id = refchange_data["ref"]["displayId"]
        rc.from_hash = refchange_data["fromHash"]
        rc.to_hash = refchange_data["toHash"]
        rc.typ = refchange_data["type"]
        return rc

class PullRequest:
    def __init__(self):
        self.event = ''
        self.id = ''
        self.title = ''
        self.description = ''
        self.url = ''
        self.comment = Comment()
        self.reviewers = []
        self.source = Ref()
        self.destination = Ref()

    @classmethod
    def from_bb_server_data(cls, data):
        pr_data = data["pullRequest"]
        pr = PullRequest()
        pr.event = data["eventKey"].split(":")[-1]
        pr.id = str(pr_data["id"])
        pr.title = pr_data.get("title")
        pr.description = pr_data.get("description")
        pr.url = pr_data["links"]["self"][0]["href"]
        pr.reviewers = [User.from_bb_data(u["user"]) for u in pr_data["reviewers"]]

        pr.source = Ref.from_bb_data(pr_data["fromRef"])
        pr.destination = Ref.from_bb_data(pr_data["toRef"])

        if data["eventKey"].startswith("pr:comment:"):
            pr.comment = Comment.from_bb_data(data)

        return pr

class Push:
    def __init__(self):
        self.repository = Repository()
        self.changes = []

    @classmethod
    def from_bb_data(cls, data):
        p = Push()
        p.repository = Repository.from_bb_data(data["repository"])
        p.changes = [RefChange.from_bb_data(rc) for rc in data["changes"]]

        return p

def readConfig():
    """
    Reads config.json to get configuration settings
    """
    d = json.load(open('config.json'))

    global application_host, application_port, application_debug
    application_host = d["application"]["host"]
    application_port = d["application"]["port"]
    application_debug = d["application"]["debug"]

    global error_color, alert_color, success_color
    error_color = d["colors"]["error"]
    alert_color = d["colors"]["alert"]
    success_color = d["colors"]["success"]

    global mattermost_url, mattermost_user, mattermost_icon
    mattermost_url = d["mattermost"]["server_url"]
    mattermost_user = d["mattermost"]["post_user_name"]
    mattermost_icon = d["mattermost"]["post_user_icon"]

    global bitbucket_url, bitbucket_ignore_comments
    bitbucket_url = d["bitbucket"]["server_url"]
    bitbucket_ignore_comments = d["bitbucket"]["ignore_comments"]


def get_event_name(event_key):
    """
    Converts event to friendly output
    """
    event_out = helpers.bitbucket_server_event_names.get(event_key)
    if event_out is None:
        raise KeyError('Unsupported event type!')
    return event_out

def get_event_action(event_key):
    """
    Converts event to friendly output
    """
    event_out = helpers.bitbucket_server_event_actions.get(event_key)
    if event_out is None:
        raise KeyError('Unsupported event type!')
    return event_out

def get_event_action_text(event_key):
    """
    Converts event to friendly output
    """
    event_out = helpers.bitbucket_cloud_event_actions.get(event_key)
    if event_out is None:
        raise KeyError('Unsupported event type!')
    return event_out

def process_payload_server(hook_path, data):
    """
    Reads Bitbucket JSON payload and converts it into Mattermost friendly
    message attachement format
    https://confluence.atlassian.com/bitbucketserver/event-payload-938025882.html
    """

    action = get_event_action(data["eventKey"])

    actor = User.from_bb_data(data["actor"])

    attachment = Attachment()
    attachment.author_name = actor.display_name
    attachment.author_icon = actor.avatar
    attachment.author_link = actor.url

    if data["eventKey"].startswith('pr:'):
        pr = PullRequest.from_bb_server_data(data)

        attachment.text = "%s `<%s>` %s `%s`. [(open)](%s)" \
                          % (actor.display_name, actor.email, action, pr.title, pr.url)
        attachment.color = success_color

        description_field = AttachmentField()
        description_field.title = "Description"
        description_field.value = pr.description
        attachment.fields.append(description_field)

        reviewers_field = AttachmentField()
        reviewers_field.title = "Reviewers"
        reviewers_field.value = ", ".join(["@" + r.name for r in pr.reviewers])
        attachment.fields.append(reviewers_field)

        source_field = AttachmentField()
        source_field.title = "Source"
        source_field.value = "%s\n%s" % (pr.source.repository.name, pr.source.display_id)
        attachment.fields.append(source_field)

        destination_field = AttachmentField()
        destination_field.title = "Destination"
        destination_field.value = "%s\n%s" % (pr.destination.repository.name, pr.destination.display_id)
        attachment.fields.append(destination_field)

        if data["eventKey"].startswith('pr:comment'):
            comment_field = AttachmentField()
            comment_field.short = False
            comment_field.title = "Comment"
            comment_field.value = pr.comment.text
            attachment.fields.append(comment_field)

    elif data["eventKey"].startswith('repo:refs_changed'):
        p = Push.from_bb_data(data)
        commit_url_base = p.repository.url[0:-6] + "commits"
        branches = ",".join(["[%s](%s?until=%s)" % (c.display_id, commit_url_base, c.id) for c in p.changes])
        attachment.pretext = "Push on [%s](%s) branch %s by %s `<%s>` (%d commit/s)." \
                          % (p.repository.name, p.repository.url, branches, actor.display_name, actor.email, len(p.changes))
        attachment.color = success_color

        for c in p.changes:
            commit_field = AttachmentField()
            commit_field.short = False
            commit_link = commit_url_base + "/" + c.to_hash
            commit_field.value = "[%s](%s): %s - %s" % (c.to_hash[0:10], commit_link, c.display_id, actor.name) # TODO: Fix commit message and commiter
            attachment.fields.append(commit_field)

    elif data["eventKey"].startswith('repo:comment'):
        c = Comment.from_bb_data(data)
        commit_url_base = c.repository.url[0:-6] + "commits/"
        attachment.pretext = "%s <%s> %s [%s](%s)" \
                             % (actor.display_name, actor.email, action, c.commit[0:11], commit_url_base + c.commit)
        attachment.color = success_color
        comment_field = AttachmentField()
        comment_field.short = False
        comment_field.title = "Comment"
        comment_field.value = c.content_markup if c.content_markup != "" else c.text
        attachment.fields.append(comment_field)

    return send_attachment_webhook(hook_path, None, attachment)

def send_webhook_data(hook_path, data):
    """
    Sends message data to the Mattermost server and hook configured
    """
    response = requests.post(
        mattermost_url + "hooks/" + hook_path,
        data = json.dumps(data),
        headers = {'Content-Type': 'application/json'}
    )
    return response

def send_attachment_webhook(hook_path, text_out, attachment):
    """
    Assembles incoming text, creates JSON object for the response, and
    sends it on to the Mattermost server and hook configured
    """

    data = {
        'text': text_out,
        'username': mattermost_user,
        'icon_url': mattermost_icon,
        "attachments": [attachment.to_dict()]
    }

    print(data)

    return send_webhook_data(hook_path, data)

def send_simple_webhook(hook_path, text_out, attachment_text, attachment_color):
    """
    Assembles incoming text, creates JSON object for the response, and
    sends it on to the Mattermost server and hook configured
    """
    if len(attachment_text) > 0:
        attach_dict = {
            "color": attachment_color,
            "text": attachment_text
        }
        data = {
            'text': text_out,
            'username': mattermost_user,
            'icon_url': mattermost_icon,
            "attachments": [attach_dict]
        }
    else:
        data = {
            'text': text_out,
            'username': mattermost_user,
            'icon_url': mattermost_icon,
        }

    return send_webhook_data(hook_path, data)


"""
------------------------------------------------------------------------------------------
Flask application below
"""
readConfig()

app = Flask(__name__)

@app.route( '/hooks/<hook_path>', methods = [ 'POST' ] )
def hooks(hook_path):

    event = request.headers.get('X-Event-Key')

    if event == "diagnostics:ping":
        request_id = request.headers.get('X-Request-Id')
        response = send_simple_webhook(hook_path, "diagnostics:ping", "Bitbucket is testing the connection to Mattermost: " + request_id, alert_color)
    else:
        if len(request.get_json()) > 0:
            data = request.get_json()
            if application_debug:
                print(data)

            response = process_payload_server(hook_path, data)

    return ""

if __name__ == '__main__':
   app.run(host = application_host, port = application_port, 
           debug = application_debug)
