# Browser-assisted affiliate account setup

UCOS Layer 10 can acquire a real affiliate product and tagged link through the
authenticated Personal Browser without receiving the affiliate password or
session cookies.

## Account registration

Use the existing account registry. Put the browser profile reference in the
account's affiliate_rules:

    {
      "browser_provider": "amazon",
      "browser_account_ref": "amazon-primary",
      "marketplace": "www.amazon.com",
      "browser_required": true
    }

`browser_account_ref` is a safe profile identifier, not an Amazon username or
password. The corresponding Playwright persistent profile lives inside the
browser worker.

## Runtime flow

Layer 14 control plane -> Layer 10 AffiliateBrowserClient -> Layer 14 PersonalBrowserAffiliateGateway -> UCOS Personal Browser -> authenticated Amazon profile -> product search -> product page / SiteStripe -> tagged HTTPS affiliate URL -> Layer 10 evidence -> content/publish package.

Credentials stay inside the browser profile. UCOS never accepts or stores the affiliate password in Layer 10.

## API

Authenticated UCOS API clients can use:

- `GET /affiliate/amazon/status?account_ref=amazon-primary`
- `POST /affiliate/amazon/search` with `{ "account_ref": "amazon-primary", "query": "coffee maker" }`

The search endpoint returns `state=verified` only after a real HTTPS Amazon URL with an Associates tag is observed through the browser workflow. Untagged or synthetic URLs fail closed.

## One-time account login

The browser profile must first be signed in to the Amazon account that owns the Associates account. Amazon documents that SiteStripe appears when the Amazon session corresponds to the Associates account, and SiteStripe can generate tagged links from the product page.

UCOS deliberately does not automate password entry or CAPTCHA/anti-bot bypass.

## Persistence requirement

The browser profile is persistent for the lifetime of the worker filesystem. For production account sessions to survive Render deploys/restarts, the browser service needs durable storage for `UCOS_BROWSER_PROFILE_DIR`. Without durable storage, the account must be authenticated again after the profile is lost.

## Compliance

Affiliate links must remain the real links returned by the approved affiliate workflow. UCOS must not fabricate tags, alter Amazon-served content, or create artificial clicks. Affiliate disclosures should be included in the publishing package.