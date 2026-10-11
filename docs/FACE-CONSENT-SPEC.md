# face-consent.txt: A Machine-Readable Consent Manifest for Facial Imagery

## Motivation

Protective perturbations degrade gracefully to nothing under web acquisition
(see the paper's collapse curves); consent infrastructure does not. A consent
statement that travels *with* the image through the funnel survives every tier
by construction. `face-consent.txt` is to face photographs what `robots.txt` is
to crawlers: a plain-text, machine-readable, versioned manifest that a site
serves at a well-known location, declaring which facial images may be used for
which purposes.

## File location and discovery

A site publishes the manifest at:

```
https://<host>/.well-known/face-consent.txt
```

Fetchers that harvest images SHOULD fetch this URL once per host per crawl
session. A 404 means "no machine-readable consent; treat as all-default-deny
for personalization uses under the default policy below."

## Grammar

The file is UTF-8 plain text. Lines starting with `#` are comments. A
directive is `Key: Value`. Indented lines (two spaces) belong to the most
recent block header.

Top-level directives:

- `Consent-Version: 1.0` (required)
- `Contact: <mailto or url>` (required)
- `Applies-To: <path prefix>` (repeatable; default `/`)
- `Default-Policy: allow|deny` (default `deny` for personalization uses)

Block header (repeatable):

- `Identity-Block: <local id>` — begins a per-subject record.

Block directives:

- `Subject-Hash: sha256-<hex>` — salted hash of the subject's identity anchor
  (salt known to the site operator; prevents trivially linking hashes across
  sites).
- `Images: <glob>` (repeatable) — path globs the block covers.
- `Allowed-Uses: <use, use, ...>` — comma-separated tokens from the use
  registry.
- `Denied-Uses: <use, use, ...>` — takes precedence over Allowed-Uses.
- `Expiry: <ISO-8601 date>` — after this date the block is inactive.
- `Revocation: <url>` — machine-readable revocation endpoint.
- `Signature: ed25519:<base64>` — detached signature over the block's
  canonical serialization, keyed by the subject (proof of consent origin) or
  the site operator (proof of hosting integrity). Either is optional; both is
  best.

## Use registry (initial tokens)

`recognition-accuracy`, `research-aggregate`, `security-fraud`,
`editorial`, `personalization`, `customization`, `fine-tuning`,
`embedding-extraction`, `training-generative`, `any`

Tokens are case-insensitive. `fine-tuning` and `embedding-extraction` are the
two uses implicated by DreamBooth-LoRA and zero-shot adapter attacks; a
manifest that omits them from `Allowed-Uses` denies them under
`Default-Policy: deny`.

## Decision procedure

1. Fetch and parse the manifest; reject malformed files entirely (deny).
2. Drop expired blocks; check `Applies-To` against the target path.
3. If the target path matches an `Images` glob of an active block, consult
   `Denied-Uses` then `Allowed-Uses`; a use listed in neither follows
   `Default-Policy`.
4. If no block matches, follow `Default-Policy`.
5. Log the decision as `(decision, rule-source, manifest-hash)` so that a
   scraper can *prove* which consent it acted on.

## Scope and non-goals

The manifest is a technical expression of claims; it is not law. Enforcement
hooks (takedown flows, audits) are legal and social. What the format buys is
that consent becomes *machine-checkable at acquisition time* — the layer where
our measurements show all perturbation-based defenses collapse.
