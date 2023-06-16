from random import randint

from Classes import MISSING, ShakeCommand, _

############
#

numbers = {
    1: "one",
    2: "two",
    3: "three",
    4: "four",
    5: "five",
    6: "six",
    7: "seven",
    8: "eight",
    9: "nine",
}


class command(ShakeCommand):
    def __init__(self, ctx, start: int = 1, end: int = 6):
        super().__init__(ctx)
        self.end: int = end
        self.start: int = start

    async def __await__(self):
        rolled = randint(self.start, self.end)

        if 0 < rolled < 10:
            rolled = getattr(self.bot.emojis.dice, numbers.get(rolled), MISSING)
            assert not rolled is MISSING

        return await self.ctx.chat(embed=rolled)


#
############
