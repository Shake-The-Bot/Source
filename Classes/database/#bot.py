############
#
from Classes.database import db
########
#   locale
class LOCALE(db.Table):
    id = db.Column(db.Integer(big=True), primary_key=True)
    locale = db.Column(db.String(), default=None)
########
#
class FREEGAMES(db.Table):
    id = db.Column(db.Integer(big=True), primary_key=True)
    games = db.Column(db.Array(db.String()), default=None)
########
#   per user & guild
class COMMANDS(db.Table):
    id = db.Column(db.Integer(big=True), primary_key=True)
    used_commands = db.Column(db.Integer(big=True), index=True, default=0)
    type = db.Column(db.String())
    rank = db.Column(db.Integer, default=0)
########
#
class RTFM(db.Table):
    id = db.PrimaryKeyColumn()
    user_id = db.Column(db.Integer(big=True), unique=True, index=True)
    count = db.Column(db.Integer(), default=1)
#########
#
class BLOCKED(db.Table):
    id = db.Column(db.Integer(big=True), primary_key=True)
    time = db.Column(db.Datetime(timezone=True), default=None)
    reason = db.Column(db.String(), default='Automoderation')