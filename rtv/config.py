"""
Global configuration settings
"""

unicode = True

# Default colors
# Colors handle text style like bold, italic etc..
default_colors = {

    # Globals / Structure
    'Background': (-1, -1),
    'HeaderBackground': (0, 14),
    'UserName': (16, 14, 2097152),
    'CurrentSub': (16, 14, 2097152),
    'ContentOrder': (16, 14),
    'Flair': (1, -1, 2097152),
    'Gold': (3, -1, 2097152),
    'Nsfw': (1, -1, 2097152),
    'ArrowNone': (-1, -1, 2097152),
    'ArrowUp': (2, -1, 2097152),
    'ArrowDown': (1, -1, 2097152),
    'Link': (4, -1, 131072),
    'LinkSeen': (5, -1, 131072),

    # Submission colors
    'SubmissionAuthor': (3, -1, 2097152),
    'SubmissionIsAuthor': (3, -1, 2097152, 131072),
    'SubmissionTitle': (-1, -1, 2097152),
    'SubmissionScore': (-1, -1),
    'SubmissionCreated': (-1, -1),
    'SubmissionText': (-1, -1),
    'SubmissionComments': (-1, -1),
    'SubmissionCommentsText': (-1, -1),
    'SubmissionMoreComments': (-1, -1),
    'SubmissionMoreCommentsCount': (14, -1),
    'SubmissionSubReddit': (3, -1, 2097152),

    # Subreddit colors
    'SubRedditTitle': (-1, -1, 2097152),
    'SubRedditScore': (-1, -1),
    'SubRedditCreated': (-1, -1),
    'SubRedditComments': (-1, -1),
    'SubRedditAuthor': (-1, -1, 2097152),
    'SubRedditIsAuthor': (2, -1, 2097152),
    'SubRedditSource': (3, -1)

}
# Levels definition
levels = [
    (9, -1),
    (10, -1),
    (11, -1),
    (12, -1),
    (13, -1),
    (14, -1)
]
# Aliases to help for specifics / forced colors
color_aliases = {
    "BOLD": 2097152,
    "UNDERLINE": 131072
}
