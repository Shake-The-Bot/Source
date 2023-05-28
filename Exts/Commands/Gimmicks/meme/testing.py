############
#
from Classes import _
from Classes import ShakeContext, ShakeBot, ShakeEmbed
from Classes.reddit import Submission
from discord import PartialEmoji
########
#
class command():
    def __init__(self, ctx: ShakeContext, subreddit: str):
        self.bot: ShakeBot = ctx.bot
        self.ctx: ShakeContext = ctx
        self.subreddit = subreddit

    def format(self, post: Submission):
        preview = post.__dict__['preview']['images'][0] if bool(len(post.__dict__['preview']['images'])) else None
        image = preview['source']['url'] if preview else None
        if image is None:
            return None
        embed = ShakeEmbed()
        embed.set_author(
            icon_url=PartialEmoji(animated=True, name='meme', id=952690616754655293).url,
            name=_('„{title}“ by {author}').format(title=str(post.title), author=post.author.name)
        )
        embed.description = '*'+ _("Like this meme? Check out others at \n{subreddit}").format(
            subreddit='https://www.reddit.com/r/'+ str(self.subreddit)) +'*'
        embed.set_image(url=image)
        return embed

    async def __await__(self):
        if not bool(len(self.bot.reddit.posts)):
            await self.ctx.defer(ephemeral=False)
        embed = None
        while embed is None:
            post: Submission = await self.bot.reddit.get_post(ctx=self.ctx, subreddit=self.subreddit)
            embed = self.format(post)
        await self.ctx.smart_reply(embed=embed)

#
############