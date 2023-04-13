############
#
from Classes.database import db
########
#
class LEVEL(db.Table):
    guild_id = db.Column(db.Integer(big=True), primary_key=True)
    TURN = db.Column(db.Boolean(), default=False, name='turn')

    default_multiplication = db.Column(db.Float(), default=1) # >1

    voice_gain = db.Column(db.Boolean(), default=False)
    voice_multiplication = db.Column(db.Float(), default=1) # >1

    reaction_gain = db.Column(db.Boolean(), default=False)
    reaction_multiplication = db.Column(db.Float(), default=1) # >1
    
    # level-channel
    channel_notification = db.Column(db.Boolean(), default=False)
    channel_id = db.Column(db.Integer(big=True))
    channel_messages = db.Column(db.Array(db.String()), default=None)
    
    # last_event-channel
    direct_notification = db.Column(db.Boolean(), default=False)
    direct_messages = db.Column(db.Array(db.String()), default=None)
########
#
class FREEGAMES(db.Table):
    channel_id = db.Column(db.Integer(big=True), index=True, primary_key=True)
    guild_id = db.Column(db.Integer(big=True))

    stores = db.Column(db.Array(db.String()), default=None) # {'steam', 'epicgames', 'gog'}
########
#
class WELCOME(db.Table):
    guild_id = db.Column(db.Integer(big=True), primary_key=True)
    TURN = db.Column(db.Boolean(), default=False, name='turn')
    
    captcha = db.Column(db.Boolean(), default=False)

    roles = db.Column(db.Array(db.Integer()), default=None)
########
#
class TEMPVOICE(db.Table):
    creator_id = db.Column(db.Integer(big=True), primary_key=True) # creator
    guild_id = db.Column(db.Integer(big=True))

    TURN = db.Column(db.Boolean(), default=False, name='turn')

    interface_id = db.Column(db.Integer(big=True), unique=True)
    category_id = db.Column(db.Integer(big=True), default=None)
    webhook_url = db.Column(db.String(), default=None)
    # default
    prefix = db.Column(db.String(), default='📞︱')
    suffix = db.Column(db.String(), default=None)
    locked = db.Column(db.Boolean(), default=False)
    user_limit = db.Column(db.Integer(), default=None)
########
#
class COUNTING(db.Table):
    channel_id = db.Column(db.Integer(big=True), primary_key=True)
    guild_id = db.Column(db.Integer(big=True))
    
    TURN = db.Column(db.Boolean(), default=False, name='turn')

    hardcore = db.Column(db.Boolean(), default=False)
    numbersonly = db.Column(db.Boolean(), default=True)
    goal = db.Column(db.Integer, default=None)
########
#
class ABOVEME(db.Table):
    channel_id = db.Column(db.Integer(big=True), primary_key=True)
    guild_id = db.Column(db.Integer(big=True))
    
    TURN = db.Column(db.Boolean(), default=False, name='turn')
########
#
class ONEWORD(db.Table):
    channel_id = db.Column(db.Integer(big=True), primary_key=True)
    guild_id = db.Column(db.Integer(big=True))
    
    TURN = db.Column(db.Boolean(), default=False, name='turn')
#
#############