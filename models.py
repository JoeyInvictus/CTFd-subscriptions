from flask import Blueprint
from CTFd.models import Challenges, Users, db
from CTFd.plugins.challenges import CHALLENGE_CLASSES, BaseChallenge
from sqlalchemy.ext.hybrid import hybrid_property

class SubscriptionChallengeModel(Challenges):
    __mapper_args__ = {"polymorphic_identity": "subscription"}
    id = db.Column(
        db.Integer, db.ForeignKey("challenges.id", ondelete="CASCADE"), primary_key=True
    )
    subscription_level = db.Column(db.String(32), default='freemium')

    def __init__(self, *args, **kwargs):
        super(SubscriptionChallengeModel, self).__init__(**kwargs)


class SubscriptionUserModel(Users):
    __mapper_args__ = {
    "polymorphic_identity": "subscriptionuser",
    }
    id = db.Column(db.Integer, primary_key=True)
    subscription_level = db.Column(db.String(32), default='freemium')
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"))
    user = db.relationship("Users", foreign_keys="SubscriptionUserModel.user_id", lazy="select")

    def __init__(self, *args, **kwargs):
        # Set default subscription level if not provided
        if 'subscription_level' not in kwargs:
            kwargs['subscription_level'] = 'freemium'
        super(SubscriptionUserModel, self).__init__(**kwargs)

    @hybrid_property
    def level(self):
        return self.subscription_level if self.subscription_level else 'freemium'


class SubscriptionChallenge(BaseChallenge):
    id = "subscription"  # Unique identifier used to register challenges
    name = "subscription"  # Name of a challenge type
    templates = (
        {  # Handlebars templates used for each aspect of challenge editing & viewing
            "create": "/plugins/subscription_challenges/assets/create.html",
            "update": "/plugins/subscription_challenges/assets/update.html",
            "view": "/plugins/subscription_challenges/assets/view.html",
        }
    )
    scripts = {  # Scripts that are loaded when a template is loaded
        "create": "/plugins/subscription_challenges/assets/create.js",
        "update": "/plugins/subscription_challenges/assets/update.js",
        "view": "/plugins/subscription_challenges/assets/view.js",
    }
    # Route at which files are accessible. This must be registered using register_plugin_assets_directory()
    route = "/plugins/subscription_challenges/assets/"
    # Blueprint used to access the static_folder directory.
    blueprint = Blueprint(
        "subscription_challenges",
        __name__,
        template_folder="templates",
        static_folder="assets",
    )
    challenge_model = SubscriptionChallengeModel

    @classmethod
    def read(cls, challenge):
        """
        This method is in used to access the data of a challenge in a format processable by the front end.

        :param challenge:
        :return: Challenge object, data dictionary to be returned to the user
        """
        challenge = SubscriptionChallengeModel.query.filter_by(id=challenge.id).first()
        data = {
            "id": challenge.id,
            "name": challenge.name,
            "value": challenge.value,
            "subscription_level": challenge.subscription_level,
            "description": challenge.description,
            "connection_info": challenge.connection_info,
            "next_id": challenge.next_id,
            "category": challenge.category,
            "state": challenge.state,
            "max_attempts": challenge.max_attempts,
            "type": challenge.type,
            "type_data": {
                "id": cls.id,
                "name": cls.name,
                "templates": cls.templates,
                "scripts": cls.scripts,
            },
        }
        return data
