# Subscription / role based access for CTFd

Minimal changes to CTFd required.

## Only change to challenges plugin required if using MySQL
Adding the following line to `@classmethod`:
```python
"subscription_required": challenge.subscription_required,
```

## This plugin provides you with:
- challenge mode subscription to set a level
- user management for subscriptions
- Sort of done: a management API
- Done: actual RBAC per subscription tier

### Overwriting API routes can be done like so:
Cool stuff I found out:

```python
    CTFd_API_v1.endpoints.remove('challenges_challenge')
    CTFd_API_v1.endpoints.remove('challenges_challenge_list')

    del app.view_functions['api.challenges_challenge_list']
    del app.view_functions['api.challenges_challenge']

    CTFd_API_v1.add_namespace(challenges_namespace, "/challenges")
```

You can overwrite / reregister customized API endpoints by removing the endspoints and deleting their view functions and adding the namespace again.

