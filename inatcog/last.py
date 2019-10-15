"""Module for handling recent history."""
from typing import NamedTuple
from datetime import datetime
import re

import timeago

from .api import get_observations
from .common import LOG
from .embeds import make_embed
from .obs import get_obs_fields
from .taxa import format_taxon_name

PAT_OBS = re.compile(
    r"\b(?P<url>https?://(www\.)?inaturalist\.(org|ca)/observations/(?P<obs_id>\d+))\b",
    re.I,
)


class ObsLinkMsg(NamedTuple):
    """Discord & iNat fields from a recent observation link."""

    url: str
    obs: dict
    ago: str
    name: str


def get_last_obs_msg(msgs):
    """Find recent observation link."""
    found = None

    found = next(m for m in msgs if not m.author.bot and re.search(PAT_OBS, m.content))
    LOG.info(repr(found))

    mat = re.search(PAT_OBS, found.content)
    obs_id = int(mat["obs_id"])
    url = mat["url"]
    ago = timeago.format(found.created_at, datetime.utcnow())
    name = found.author.nick or found.author.name

    results = get_observations(obs_id)["results"]
    obs = get_obs_fields(results[0]) if results else None

    return ObsLinkMsg(url, obs, ago, name)


def make_last_obs_embed(last):
    """Return embed for recent observation link."""
    embed = make_embed(url=last.url)
    summary = None

    if last:
        obs = last.obs
        taxon = obs.taxon
        if taxon:
            embed.title = format_taxon_name(taxon)
        else:
            embed.title = "Unknown"
        if obs.thumbnail:
            embed.set_thumbnail(url=obs.thumbnail)
        if obs.obs_on:
            summary = "Observed by %s on %s" % (obs.obs_by, obs.obs_on)
        else:
            summary = "Observed by %s" % obs.obs_by
    else:
        LOG.info("Deleted observation: %d", obs.obs_id)
        embed.title = "Deleted"

    embed.add_field(
        name=summary or "\u200B", value="shared %s by @%s" % (last.ago, last.name)
    )
    return embed
