"""Module to access eBird API."""
from datetime import datetime
from redbot.core import commands, Config
from ebird.api import get_observations

class EBirdCog(commands.Cog):
    """eBird commands cog"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=8008)
        default_global = {
            "region": 'CA-NS',
            "days": 30,
            "datetime_format": '%H:%M, %d %b',
        }
        self.config.register_global(**default_global)

    @commands.command()
    async def hybrids(self, ctx):
        """Report recent hybrid observations."""
        datetime_format = await self.config.datetime_format()

        records = await self.get_hybrid_observations(ctx)
        message = []
        for record in records:
            sciname = record['sciName']
            comname = record['comName']
            locname = record['locName']
            howmany = record['howMany']
            obsdt = datetime.strptime(record['obsDt'], '%Y-%m-%d %H:%M')
            line = '%d %s (%s); latest: %s from: %s' % (
                howmany,
                comname,
                sciname,
                obsdt.strftime(datetime_format),
                locname,
            )
            message.append(line)
        await ctx.send("\n".join(message))

    async def get_hybrid_observations(self, ctx):
        """Get recent hybrid observations."""
        ebird_key = await self.get_api_key(ctx)
        region = await self.config.region()
        days = await self.config.days()
        # Docs at: https://github.com/ProjectBabbler/ebird-api
        return get_observations(
            ebird_key["api_key"],
            region,
            back=days,
            category="hybrid",
            detail="simple",
            provisional=True,
        )

    async def get_api_key(self, ctx):
        """Get API key."""
        key = await self.bot.db.api_tokens.get_raw("ebird", default={"api_key": None})
        if key["api_key"] is None:
            return await ctx.send("The eBird API key has not been set.")
        return key
