from typing import List

from flask import abort, request, session
from flask_restx import Namespace, Resource

from CTFd.api.v1.helpers.request import validate_args

from CTFd.cache import clear_challenges, clear_standings
from CTFd.constants import RawEnum
from CTFd.models import (
    Users,
    db,
)
from CTFd.schemas.users import UserSchema
from CTFd.utils.decorators import admins_only
from CTFd.utils.decorators.visibility import (
    check_account_visibility
)
from CTFd.utils.email import user_created_notification
from CTFd.utils.helpers.models import build_model_filters
from CTFd.utils.user import is_admin

from .models import SubscriptionUserModel

users_namespace = Namespace("users", description="Endpoint to retrieve Users")

@users_namespace.route("")
@check_account_visibility
def test():
    print("triggered")
    print(request)
    # @users_namespace.doc(
    #     description="Endpoint to get User objects in bulk",
    #     responses={
    #         200: ("Success", "UserListSuccessResponse"),
    #         400: (
    #             "An error occured processing the provided or stored data",
    #             "APISimpleErrorResponse",
    #         ),
    #     },
    # )
    # @validate_args(
    #     {
    #         "affiliation": (str, None),
    #         "country": (str, None),
    #         "bracket": (str, None),
    #         "q": (str, None),
    #         "field": (
    #             RawEnum(
    #                 "UserFields",
    #                 {
    #                     "name": "name",
    #                     "website": "website",
    #                     "country": "country",
    #                     "bracket": "bracket",
    #                     "affiliation": "affiliation",
    #                     "email": "email",
    #                 },
    #             ),
    #             None,
    #         ),
    #     },
    #     location="query",
    # )
    print(request.method)
    if request.method == "GET":
        def get(query_args):
            q = query_args.pop("q", None)
            field = str(query_args.pop("field", None))

            if field == "email":
                if is_admin() is False:
                    return {
                        "success": False,
                        "errors": {"field": "Emails can only be queried by admins"},
                    }, 400

            filters = build_model_filters(model=Users, query=q, field=field)

            if is_admin() and request.args.get("view") == "admin":
                users = (
                    Users.query.filter_by(**query_args)
                    .filter(*filters)
                    .paginate(per_page=50, max_per_page=100, error_out=False)
                )
            else:
                users = (
                    Users.query.filter_by(banned=False, hidden=False, **query_args)
                    .filter(*filters)
                    .paginate(per_page=50, max_per_page=100, error_out=False)
                )

            response = UserSchema(view="user", many=True).dump(users.items)

            if response.errors:
                return {"success": False, "errors": response.errors}, 400

            return {
                "meta": {
                    "pagination": {
                        "page": users.page,
                        "next": users.next_num,
                        "prev": users.prev_num,
                        "pages": users.pages,
                        "per_page": users.per_page,
                        "total": users.total,
                    }
                },
                "success": True,
                "data": response.data,
            }
        get()
    elif request.method == "POST":
        @admins_only
        def post():
            print("made it post")
            req = request.get_json()
            schema = UserSchema("admin")
            response = schema.load(req)
            print("success")


            if response.errors:
                print("response")
                return {"success": False, "errors": response.errors}, 400

            db.session.add(response.data)
            db.session.commit()

            subscription_user = SubscriptionUserModel(
                user_id=response.data.id,  # Link the subscription to the created user
                subscription_level=req['subscription']  # Set the subscription level from the request
            )
            db.session.add(subscription_user)
            db.session.commit() 
            print("I just made a user, yippie!")

            if request.args.get("notify"):
                name = response.data.name
                email = response.data.email
                password = req.get("password")

                user_created_notification(addr=email, name=name, password=password)

            clear_standings()
            clear_challenges()
            print("cleared")
            response = schema.dump(response.data)
            print(response)
            return {"success": True, "data": response.data}
        post()
    return 