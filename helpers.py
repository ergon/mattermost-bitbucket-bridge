"""
Dictionary of supported Bitbucket events and output friendly format
"""
bitbucket_server_event_names = {
    "pr:comment:added": "Pull Request: Comment Added",
    "pr:comment:deleted": "Pull Request: Comment Deleted",
    "pr:comment:edited": "Pull Request: Comment Edited",
    "pr:opened": "Pull Request: Opened",
    "pr:declined": "Pull Request: Declined",
    "pr:deleted": "Pull Request: Deleted",
    "pr:merged": "Pull Request: Merged",
    "pr:modified": "Pull Request: Modified",
    "pr:approved": "Pull Request: Approved",
    "pr:unapproved": "Pull Request: Unapproved",
    "repo:refs_changed": "Repository: Updated",
    "repo:comment:added": "Repository: Commit Comment Added",
    "repo:comment:edited": "Repository: Commit Comment Edited",
    "repo:comment:deleted": "Repository: Commit Comment Deleted",
    "repo:commit_comment_created": "Repository: Commit Comment Added",
    "repo:forked": "Repository: Forked"
}

bitbucket_server_event_actions = {
    "pr:comment:added": "added comment on pull request",
    "pr:comment:deleted": "deleted comment on pull request",
    "pr:comment:edited": "edited comment on pull request",
    "pr:opened": "opened pull request",
    "pr:declined": "declined pull request",
    "pr:deleted": "deleted pull request",
    "pr:merged": "merged pull request",
    "pr:modified": "modified pull request",
    "pr:approved": "approved pull request",
    "pr:unapproved": "unapproved pull request",
    "repo:refs_changed": "updated repository",
    "repo:comment:added": "added comment on commit",
    "repo:comment:edited": "edited comment on commit",
    "repo:comment:deleted": "deleted comment on commit",
    "repo:commit_comment_created": "created comment on commit",
    "repo:forked": "forked repository"
}

bitbucket_cloud_event_actions = {
    "pullrequest:created": "{} created pull request {}",
    "pullrequest:updated": "{} updated pull request {}",
    "pullrequest:approved": ":thumbsup: {} approved pull request {}",
    "pullrequest:unapproved": "{} unapproved pull request {}",
    "pullrequest:merged": ":tada: {} merged pull request {}",
    "pullrequest:declined": "{} declined pull request {}",
    "pullrequest:deleted": "{} deleted pull request {}",
    "pullrequest:comment_created": "{} added a comment to pull request {}",
    "pullrequest:comment_updated": "{} updated a comment to pull request {}",
    "pullrequest:comment_deleted": "{} deleted a comment to pull request {}",
    "repo:push": "{} Repository: Code changes pushed by: {}"
}
