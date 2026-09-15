"""Bootstrap minimal, source-attributed API constraints.

This is deliberately not a copy of platform community guidelines. It records only
technical publishing constraints that UCOS can enforce deterministically; richer
policy snapshots can be added without changing the pipeline.
"""
from .policy_registry import PolicyRegistry, PlatformPolicy

SOURCES={
 "facebook":"https://developers.facebook.com/docs/pages-api/",
 "instagram":"https://developers.facebook.com/docs/instagram-platform/content-publishing/",
 "pinterest":"https://developers.pinterest.com/docs/work-with-organic-content-and-users/create-boards-and-pins/",
 "youtube":"https://developers.google.com/youtube/v3/docs/videos/insert",
 "tiktok":"https://developers.tiktok.com/docs/en/content-posting-api-reference-direct-post",
}

def ensure_default_snapshots(registry=None):
    registry=registry or PolicyRegistry()
    defaults={
      "facebook":{"content_types":["post","photo"]},
      "instagram":{"content_types":["post","photo","video"]},
      "pinterest":{"content_types":["photo"]},
      "youtube":{"content_types":["video"],"max_length":5000},
      "tiktok":{"content_types":["photo","video"],"max_length":2200},
    }
    for platform,constraints in defaults.items():
        if registry.get(platform) is None:
            registry.register(PlatformPolicy(platform,"api-constraints-2026-09",SOURCES[platform],constraints=constraints,content_gate={"scope":"technical_api_constraints"}))
    return registry
