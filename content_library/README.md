# content_library

This is where future content gets queued for publishing. Nothing here is
committed by default except the example/schema file:

- `queue.example.yaml` — schema reference, copy to `queue.yaml` to activate.
- `queue.yaml` — the real, active queue (git-ignored — may contain
  unpublished captions/media links you don't want public before they post).

Each entry represents one Instagram post. See `queue.example.yaml` for the
full field reference. `topics` drives hashtag selection (`insta_man/hashtags`);
`extra_hashtags` are always included as-is.
