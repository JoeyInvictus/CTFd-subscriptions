
from CTFd.plugins import register_plugin_assets_directory
from CTFd.plugins.challenges import CHALLENGE_CLASSES
from CTFd.plugins.migrations import upgrade
from CTFd.utils.plugins import override_template
from CTFd.forms import Forms,BaseForm
from flask_restx import Namespace, Resource
from pathlib import Path

from .models import SubscriptionChallenge
from .views import users_listing
from .users import UserCreateForm
from .api import test

def load(app):
    '''Register the plugin'''
    app.db.create_all()
    upgrade(plugin_name="subscription")
    CHALLENGE_CLASSES["subscription"] = SubscriptionChallenge
    register_plugin_assets_directory(
        app, base_path="/plugins/subscription_challenges/assets/"
    )
    
    '''Overwrite the existing template'''
    dir_path = Path(__file__).parent.resolve()
    users_template_path = dir_path / 'templates' / 'users.html'
    override_template('admin/users/users.html', open(users_template_path).read())

    '''Overwrite the existing template'''
    create_template_path = dir_path / 'templates' / 'create.html'
    override_template('admin/modals/users/create.html', open(create_template_path).read())

    '''overwrite the user listing functionality'''
    app.view_functions['admin.users_listing'] = users_listing
    
    #app.view_functions['api.users_user_list'] = test

    '''Init the user creat form'''
    Forms.self.UserCreateForm = UserCreateForm
