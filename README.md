# Subscription / role based access for CTFd

Minimal changes to CTFd required.

## Changes to CTFd

This plugin executes a migration that edits the challenge and user tables native to vanilla CTFd


## This plugin provides you with:
- challenge mode subscription to set a level
- user management for subscriptions
- works via the API
- actual RBAC per subscription tier

### Overwriting API routes
We are overwriting specific API routes with our custom ones in order to make this plugin function.

```python
    CTFd_API_v1.endpoints.remove('challenges_challenge')
    CTFd_API_v1.endpoints.remove('challenges_challenge_list')

    del app.view_functions['api.challenges_challenge_list']
    del app.view_functions['api.challenges_challenge']

    CTFd_API_v1.add_namespace(challenges_namespace, "/challenges")
```

You can overwrite / reregister customized API endpoints by removing the endspoints and deleting their view functions and adding the namespace again.

