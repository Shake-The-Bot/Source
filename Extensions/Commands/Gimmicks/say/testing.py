from re import findall

from Classes import ShakeCommand, _

url_patterns = [
    "^https?:\\/\\/(?:www\\.)?[-a-zA-Z0-9@:%._\\+~#=]{1,256}\\.[a-zA-Z0-9()]{1,6}\\b(?:[-a-zA-Z0-9()@:%_\\+.~#?&\\/=]*)$",
    "^[-a-zA-Z0-9@:%._\\+~#=]{1,256}\\.[a-zA-Z0-9()]{1,6}\\b(?:[-a-zA-Z0-9()@:%_\\+.~#?&\\/=]*)$",
]


############
#


class command(ShakeCommand):
    def __init__(self, ctx, text: str, reply: bool):
        super().__init__(ctx)
        self.text: str = text
        self.reply: bool = reply

    async def __await__(self):
        for pattern in url_patterns:
            if bool(findall(pattern, self.text)):
                return await self.ctx.chat(
                    _("Hey, {user}. Urls or invites aren't allowed!").format(
                        user=self.ctx.author.mention
                    )
                )
        if self.reply:
            return await self.ctx.reply(self.text)
        return await self.ctx.chat(self.text)


#
############
