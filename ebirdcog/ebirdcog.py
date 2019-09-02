"""Module to access eBird API."""
from datetime import datetime
from redbot.core import commands, checks, Config
from ebird.api import get_observations

class ObsRecord(dict):
    """A human-readable observation record."""
    def __init__(self, datetime_format='%H:%M, %d %b, %Y', **kwargs):
        self.datetime_format = datetime_format
        super().__init__(**kwargs)

    def __getitem__(self, key):
        """Reformat datetime into human-readable format."""
        val = super().__getitem__(key)
        if key == 'obsDt':
            return datetime.strptime(val, '%Y-%m-%d %H:%M').strftime(self.datetime_format)
        return val

class EBirdCog(commands.Cog):
    """An eBird commands cog."""
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=8008)
        self.config.register_global(
            region='CA-NS',
            days=30,
            datetime_format='%H:%M, %d %b'
        )

    @commands.group()
    async def ebird(self, ctx):
        """Access the eBird platform."""
        pass # pylint: disable=unnecessary-pass

    @ebird.command()
    @checks.is_owner()
    async def checkdays(self, ctx):
        """Checks days setting."""
        days = await self.config.days()
        await ctx.send('eBird days is {}.'.format(days))

    @ebird.command()
    @checks.is_owner()
    async def checkregion(self, ctx):
        """Checks region setting."""
        region = await self.config.region()
        await ctx.send('eBird region is {}.'.format(region))

    @ebird.command()
    async def hybrids(self, ctx):
        """Reports recent hybrid observations."""
        records = await self.get_hybrid_observations(ctx) or []
        if records is False:
            return
        fmt = await self.config.datetime_format()
        for record in records:
            rec = ObsRecord(fmt, **record)
            msg = (
                '{comName} ({sciName});'
                '{howMany} observed at {obsDt}, from {locName}'
            ).format_map(rec)
            await ctx.send(msg)
        if not records:
            days = await self.config.days()
            await ctx.send("No hybrids observed in the past %d days." % days)

    @ebird.command()
    @checks.is_owner()
    async def setregion(self, ctx, value: str):
        """Sets region."""
        await self.config.region.set(value)
        await ctx.send('eBird region has been changed.')

    @ebird.command()
    @checks.is_owner()
    async def setdays(self, ctx, value: int):
        """Sets days considered recent (1 through 30; default: 30)."""
        days = int(value)
        if days in range(1, 31):
            await self.config.days.set(days)
            await ctx.send('eBird days has been changed.')
        else:
            await ctx.send('eBird days must be a number from 1 through 30.')


    async def get_hybrid_observations(self, ctx):
        """Gets recent hybrid observations."""
        ebird_key = await self.get_api_key(ctx)
        if ebird_key is None:
            return False
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
        """Gets API key."""
        key = await self.bot.db.api_tokens.get_raw("ebird", default={"api_key": None})
        if key["api_key"] is None:
            await ctx.send(
                "The eBird API key is not set yet.\n"
                "1. Get one here:\n"
                "   https://ebird.org/api/keygen\n"
                "2. Set the key:\n"
                "   [p]set api ebird api_key,your-key-goes-here"
            )
            return None
        return key
