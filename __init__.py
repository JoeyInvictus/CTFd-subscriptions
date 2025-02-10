
from CTFd.plugins import register_plugin_assets_directory
from CTFd.plugins.challenges import CHALLENGE_CLASSES
from CTFd.plugins.migrations import upgrade
from CTFd.utils.plugins import override_template
from pathlib import Path

from .models import SubscriptionChallenge
from .views import users_listing



def load(app):
    app.db.create_all()
    upgrade(plugin_name="subscription")
    CHALLENGE_CLASSES["subscription"] = SubscriptionChallenge
    register_plugin_assets_directory(
        app, base_path="/plugins/subscription_challenges/assets/"
    )
    
    dir_path = Path(__file__).parent.resolve()
    template_path = dir_path / 'templates' / 'users.html'
    override_template('admin/users/users.html', open(template_path).read())

    app.view_functions['admin.users_listing'] = users_listing
