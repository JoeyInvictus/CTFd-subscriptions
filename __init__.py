
from CTFd.utils.plugins import override_template
from CTFd.forms import Forms
from CTFd.plugins.migrations import upgrade
from pathlib import Path
from CTFd.api import CTFd_API_v1

from .forms import UserCreateForm, UserEditForm
from .challengeapi import challenges_namespace
from .userapi import users_namespace

def load(app):
    upgrade() #required for upgrading tables
    app.db.create_all() # create from models if present

    '''Overwrite the existing templates'''
    dir_path = Path(__file__).parent.resolve()

    users_template_path = dir_path / 'templates' / 'users.html'
    override_template('admin/users/users.html', open(users_template_path).read())

    create_template_path = dir_path / 'templates' / 'create.html'
    override_template('admin/modals/users/create.html', open(create_template_path).read())

    edit_template_path = dir_path / 'templates' / 'edit.html'
    override_template('admin/modals/users/edit.html', open(edit_template_path).read())

    create_chall_template_path = dir_path / 'templates' / 'challenges' / 'create.html'
    override_template('admin/challenges/create.html', open(create_chall_template_path).read())

    chall_template_path = dir_path / 'templates' / 'challenges' / 'challenges.html'
    override_template('admin/challenges/challenges.html', open(chall_template_path).read())

    update_chall_template_path = dir_path / 'templates' / 'challenges' / 'update.html'
    override_template('admin/challenges/update.html', open(update_chall_template_path).read())
    '''End template override'''    
    
    '''Overwrite API endpoints'''
    CTFd_API_v1.endpoints.remove('challenges_challenge')
    CTFd_API_v1.endpoints.remove('challenges_challenge_list')
    del app.view_functions['api.challenges_challenge_list']
    del app.view_functions['api.challenges_challenge']
    CTFd_API_v1.add_namespace(challenges_namespace, "/challenges")

    CTFd_API_v1.endpoints.remove('users_user_public')
    del app.view_functions['api.users_user_public']
    CTFd_API_v1.add_namespace(users_namespace, "/users")

    '''Init the user create form'''
    Forms.self.UserCreateForm = UserCreateForm
    Forms.self.UserEditForm = UserEditForm

    print(app.view_functions)