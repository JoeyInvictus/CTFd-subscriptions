from pathlib import Path

from CTFd.utils.plugins import override_template
from CTFd.forms import Forms
from CTFd.plugins.migrations import upgrade
from CTFd.api import CTFd_API_v1

from .forms import UserCreateForm, UserEditForm
from .challengeapi import challenges_namespace
from .userapi import users_namespace

def load(app):
    '''
    This function is called when the plugin is loaded
    '''
    upgrade() # required for upgrading tables
    app.db.create_all() # create from models if present

    # Overwrite the existing templates
    dir_path = Path(__file__).parent.resolve()

    # override the users template
    users_template_path = dir_path / 'templates' / 'users.html'
    override_template('admin/users/users.html', open(users_template_path).read())

    # override the user creation template
    create_template_path = dir_path / 'templates' / 'create.html'
    override_template('admin/modals/users/create.html', open(create_template_path).read())

    # override the user modification template
    edit_template_path = dir_path / 'templates' / 'edit.html'
    override_template('admin/modals/users/edit.html', open(edit_template_path).read())

    # override the challenge creation template
    create_chall_template_path = dir_path / 'templates' / 'challenges' / 'create.html'
    override_template('admin/challenges/create.html', open(create_chall_template_path).read())

    # override the challenge listing template
    chall_template_path = dir_path / 'templates' / 'challenges' / 'challenges.html'
    override_template('admin/challenges/challenges.html', open(chall_template_path).read())

    # override the challenge modification template
    update_chall_template_path = dir_path / 'templates' / 'challenges' / 'update.html'
    override_template('admin/challenges/update.html', open(update_chall_template_path).read())
  
    # this trick is used to overwrite arbitrary API endpoints in order to
    # introduce new functionality

    # this removes the API endpoints for challenge create/update/delete and list
    CTFd_API_v1.endpoints.remove('challenges_challenge')
    CTFd_API_v1.endpoints.remove('challenges_challenge_list')
    # this removes them from all flask view functions
    del app.view_functions['api.challenges_challenge_list']
    del app.view_functions['api.challenges_challenge']
    # and then we re-register our own
    CTFd_API_v1.add_namespace(challenges_namespace, "/challenges")

    # removed the users endpoint
    CTFd_API_v1.endpoints.remove('users_user_public')
    # deletes the flask view function
    del app.view_functions['api.users_user_public']
    # re-registers our own
    CTFd_API_v1.add_namespace(users_namespace, "/users")

    # also link to our user creation and modification forms
    Forms.self.UserCreateForm = UserCreateForm
    Forms.self.UserEditForm = UserEditForm
