from typing import List

from flask import abort, request, session
from flask_restx import Namespace, Resource

from CTFd.api.v1.helpers.request import validate_args
from CTFd.api.v1.helpers.schemas import sqlalchemy_to_pydantic
from CTFd.api.v1.schemas import (
    APIDetailedSuccessResponse,
    PaginatedAPIListSuccessResponse,
)
from CTFd.cache import clear_challenges, clear_standings, clear_user_session
from CTFd.constants import RawEnum
from CTFd.models import (
    Awards,
    Notifications,
    Solves,
    Submissions,
    Tracking,
    Unlocks,
    Users,
    db,
)
from CTFd.schemas.awards import AwardSchema
from CTFd.schemas.submissions import SubmissionSchema
from CTFd.utils.config import get_mail_provider
from CTFd.utils.decorators import admins_only, authed_only, ratelimit
from CTFd.utils.decorators.visibility import (
    check_account_visibility,
    check_score_visibility,
)
from CTFd.utils.email import sendmail, user_created_notification
from CTFd.utils.helpers.models import build_model_filters
from CTFd.utils.security.auth import update_user
from CTFd.utils.user import get_current_user, get_current_user_type, is_admin

from . userschema import UserSchema

users_namespace = Namespace("users", description="Endpoint to retrieve Users")


UserModel = sqlalchemy_to_pydantic(Users)
TransientUserModel = sqlalchemy_to_pydantic(Users, exclude=["id"])


class UserDetailedSuccessResponse(APIDetailedSuccessResponse):
    data: UserModel


class UserListSuccessResponse(PaginatedAPIListSuccessResponse):
    data: List[UserModel]


users_namespace.schema_model(
    "UserDetailedSuccessResponse", UserDetailedSuccessResponse.apidoc()
)

users_namespace.schema_model(
    "UserListSuccessResponse", UserListSuccessResponse.apidoc()
)


@users_namespace.route("/<int:user_id>")
@users_namespace.param("user_id", "User ID")
class UserPublic(Resource):
    @check_account_visibility
    @users_namespace.doc(
        description="Endpoint to get a specific User object",
        responses={
            200: ("Success", "UserDetailedSuccessResponse"),
            400: (
                "An error occured processing the provided or stored data",
                "APISimpleErrorResponse",
            ),
        },
    )
    def get(self, user_id):
        user = Users.query.filter_by(id=user_id).first_or_404()

        if (user.banned or user.hidden) and is_admin() is False:
            abort(404)

        user_type = get_current_user_type(fallback="user")
        response = UserSchema(view=user_type).dump(user)

        if response.errors:
            return {"success": False, "errors": response.errors}, 400

        response.data["place"] = user.place
        response.data["score"] = user.score

        return {"success": True, "data": response.data}

    @admins_only
    @users_namespace.doc(
        description="Endpoint to edit a specific User object",
        responses={
            200: ("Success", "UserDetailedSuccessResponse"),
            400: (
                "An error occured processing the provided or stored data",
                "APISimpleErrorResponse",
            ),
        },
    )
    def patch(self, user_id):
        user = Users.query.filter_by(id=user_id).first_or_404()
        data = request.get_json()
        data["id"] = user_id

        # Admins should not be able to ban themselves
        if data["id"] == session["id"] and (
            data.get("banned") is True or data.get("banned") == "true"
        ):
            return (
                {"success": False, "errors": {"id": "You cannot ban yourself"}},
                400,
            )

        schema = UserSchema(view="admin", instance=user, partial=True)
        response = schema.load(data)
        if response.errors:
            return {"success": False, "errors": response.errors}, 400

        # This generates the response first before actually changing the type
        # This avoids an error during User type changes where we change
        # the polymorphic identity resulting in an ObjectDeletedError
        # https://github.com/CTFd/CTFd/issues/1794
        response = schema.dump(response.data)
        db.session.commit()
        db.session.close()

        clear_user_session(user_id=user_id)
        clear_standings()
        clear_challenges()

        return {"success": True, "data": response.data}

    @admins_only
    @users_namespace.doc(
        description="Endpoint to delete a specific User object",
        responses={200: ("Success", "APISimpleSuccessResponse")},
    )
    def delete(self, user_id):
        # Admins should not be able to delete themselves
        if user_id == session["id"]:
            return (
                {"success": False, "errors": {"id": "You cannot delete yourself"}},
                400,
            )

        Notifications.query.filter_by(user_id=user_id).delete()
        Awards.query.filter_by(user_id=user_id).delete()
        Unlocks.query.filter_by(user_id=user_id).delete()
        Submissions.query.filter_by(user_id=user_id).delete()
        Solves.query.filter_by(user_id=user_id).delete()
        Tracking.query.filter_by(user_id=user_id).delete()
        Users.query.filter_by(id=user_id).delete()
        db.session.commit()
        db.session.close()

        clear_user_session(user_id=user_id)
        clear_standings()
        clear_challenges()

        return {"success": True}
