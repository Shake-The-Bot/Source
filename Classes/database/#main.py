############
#
from Classes import db, _
########
#
class LEVEL(db.Table):
    id = db.PrimaryKeyColumn()
    user_id = db.Column(db.Integer(big=True), unique=True, index=True)
    rank = db.Column(db.Integer(), default=0)
    boost = db.Column(db.Integer(), default=1)
    level = db.Column(db.Integer(), default=0)
    points = db.Column(db.Integer(), default=0)
    npoints = db.Column(db.Integer(), default=5)
    dailypoints = db.Column(db.Integer(), default=0)
    weeklypoints = db.Column(db.Integer(), default=0)
    monthlypoints = db.Column(db.Integer(), default=0)
    allpoints = db.Column(db.Integer(), default=0)
    # config
########
#
class COUNTING(db.Table):
    channel_id = db.Column(db.Integer(big=True), index=True, primary_key=True)

    user_id = db.Column(db.Integer(big=True), name='user_id', default=None)

    count = db.Column(db.Integer, default=1)
    streak = db.Column(db.Integer, default=0)
    best_streak = db.Column(db.Integer, default=0)
########rray
#
class ABOVEME(db.Table):
    channel_id = db.Column(db.Integer(big=True), index=True, primary_key=True)

    user_id = db.Column(db.Integer(big=True), name='user_id', default=None)

    phrases = db.Column(db.Array(db.String()), default=None) # last_phrases
########
#
class ONEWORD(db.Table):
    channel_id = db.Column(db.Integer(big=True), index=True, primary_key=True)

    user_id = db.Column(db.Integer(big=True), name='user_id', default=None)
    
    words = db.Column(db.Array(db.String()), default=None) # last_word
    phrase = db.Column(db.String(), default=None) # last_phrase
    count = db.Column(db.Integer, default=0)
########
#
class TEMPVOICE(db.Table):
    channel_id = db.Column(db.Integer(big=True), index=True, primary_key=True)
    interface_id = db.Column(db.Integer(big=True))
    creator_id = db.Column(db.Integer(big=True))
    
    user_id = db.Column(db.Integer(big=True), unique=True) # owner
    time_start = db.Column(db.Datetime())
    user_limit = db.Column(db.Integer(), default=None, name='user_limit')
    privacy = db.Column(db.Boolean(), default=False)
    trusted = db.Column(db.Array(db.Integer(big=True)), default=None)
    blocked = db.Column(db.Array(db.Integer(big=True)), default=None)
    thread = db.Column(db.Boolean(), default=False)
########
#
class USERDATA(db.Table):
    user_id = db.Column(db.Integer(big=True), primary_key=True) # user_id
    first_message = db.Column(db.Array(db.Integer(big=True)), default=None)
    voicechannel_time_start = db.Column(db.Datetime(), index=True, default=None) # ändert immer
    voicechannel_time_general = db.Column(db.Interval(), index=True, default=None)
    voicechannel_time_score = db.Column(db.Interval(), index=True, default=None)
#
############