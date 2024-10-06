## Frontend

For local development:

```
make frontend-dev
```

For production:

```
make frontend
```

### Your replays are private by default

By default, you are the only one who can access to your Miyoka server,
so that your replays are kept in private.
You have to set your original password to the `PASSWORD` environment variable when you're setting up a new Miyoka server,
and you have to type the password everytime access to the website.

If you want to share your replays with a friend or a coach, you can tell them your password, so that they gain an access to your resource.
After they don't need to access your replays anymore, you should change your password to a different one,
so that your replays will be back to private again.

Optionally, you can skip the password requirement by setting `None` (String) to `PASSWORD` environment variable.
This means that anyone can view your replays.

See [Authentication without SSO](https://docs.streamlit.io/knowledge-base/deploy/authentication-without-sso) for more information.

## Group scenes by similarity

Install:

```
poetry install
```

Commands:

```
make group_scenes
```

Output:

```
# Scenes:
# `scenes/<replay-id>/<round-id>/scene-<scene-id>.mp4`

# Scenes by similarity:
# The base scene is compared against the other scenes and if a similar one is found, it's copied under the folder.
# `scenes/<base-replay-id>/<base-round-id>/scene-<base-scene-id>/<target-replay-id>-<target-round-id>-scene-<target-scene-id>.mp4`
```

Approach:

- Scene split:
    - [Clustering](https://scikit-learn.org/stable/modules/clustering.html) each scene. Centroids are the frames that contain actions e.g. LP, MP, HP, etc.
    - If action frames are close enough, they are concatenated as one scene i.e. `eps=30` of DBSCAN. 
    - Prefix and suffix frames are attached to the scene.
    - e.g. p1: ["4", "4 LP", "4 LP", "1", "1", "1", "1", "1 HP", "2"] => p1 scenes: [["4", "4 LP", "4 LP", "1"], ["1", "1 HP", "2"]]
- Vectorize scenes:
    - Extract features in Bag of Words style. Each frame is tokenized and unique-count per scene.
    - For arrow direction changes, we use bigram.
- Group scenes by similarity:
    - Calculate the similarity by the vectorized scenes.
    - We use Cosine similarity 
