############
#
from io import BytesIO
from random import choice, randrange

from discord import File, Member
from PIL import Image, ImageFilter

from Classes import ShakeCommand, ShakeEmbed, _


########
#
class command(ShakeCommand):
    def __init__(self, ctx, member: Member):
        super().__init__(ctx)
        self.member: Member = member

    async def __await__(self):
        w, h = 400, 400
        async with self.bot.session.get(self.member.avatar.url) as response:
            data = await response.read()

        _bytes = BytesIO(data)
        image = Image.open(_bytes).convert("RGBA").resize((w, h))
        image2 = Image.open("./Assets/utils/rbflag.png").resize((w, h))

        image2 = image2.resize((576, 576))
        image2 = image2.filter(ImageFilter.BoxBlur(radius=10))
        image2 = image2.rotate(randrange(0, 360), center=(288, 288))  # 350
        image2.putalpha(randrange(30, 90))
        image.paste(image2, (-88, -88), image2)
        name = "rainbow{}".format(choice([1, 2, 3]))

        with BytesIO() as image_binary:
            image.save(image_binary, "PNG")
            image_binary.seek(0)
            file = File(fp=image_binary, filename=f"{name}.png")
        embed = ShakeEmbed.default(self.ctx)
        embed.set_image(url=f"attachment://{name}.png")
        await self.ctx.chat(embed=embed, file=file)


#
############
