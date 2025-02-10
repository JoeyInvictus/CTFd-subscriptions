from flask import render_template, request, url_for
from .models import SubscriptionUserModel
from CTFd.admin import admin
from CTFd.utils.decorators import admins_only
from CTFd.models import  Tracking, Users, db


@admin.route("/admin/users")
@admins_only
def users_listing():
    q = request.args.get("q")
    field = request.args.get("field")
    page = abs(request.args.get("page", 1, type=int))
    filters = []
    users = []

    if q:
        # The field exists as an exposed column
        if Users.__mapper__.has_property(field):
            filters.append(getattr(Users, field).like("%{}%".format(q)))

    if q and field == "ip":
        users = (
            Users.query.join(Tracking, Users.id == Tracking.user_id)
            .filter(Tracking.ip.like("%{}%".format(q)))
            .order_by(Users.id.asc())
            .paginate(page=page, per_page=50, error_out=False)
        )
    else:
        # Join SubscriptionUserModel (subclass of Users)
        users = (
            db.session.query(Users, SubscriptionUserModel.subscription_level)
            .outerjoin(SubscriptionUserModel, Users.id == SubscriptionUserModel.id)
            .filter(*filters)
            .order_by(Users.id.asc())
            .paginate(page=page, per_page=50, error_out=False)
        )

    args = dict(request.args)
    args.pop("page", 1)

    return render_template(
        "admin/users/users.html",
        users=users,
        prev_page=url_for(request.endpoint, page=users.prev_num, **args),
        next_page=url_for(request.endpoint, page=users.next_num, **args),
        q=q,
        field=field,
    )
