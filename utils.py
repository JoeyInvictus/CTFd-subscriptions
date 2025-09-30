from collections import namedtuple
from sqlalchemy.sql import and_
from sqlalchemy.orm import joinedload
from CTFd.cache import cache
from CTFd.models import Challenges
from CTFd.schemas.tags import TagSchema
from CTFd.utils.helpers.models import build_model_filters


Challenge = namedtuple(
    "Challenge", ["id", "type", "name", "value", "category", "tags", "requirements"]
)

@cache.memoize(timeout=60)
def get_all_challenges(admin=False, field=None, q=None, sub=None, **query_args):
    filters = build_model_filters(model=Challenges, query=q, field=field)
    chal_q = Challenges.query

    if sub == "freemium":
        # For freemium users, get challenges that are either:
        # 1. Explicitly marked as freemium in subscription_required
        # 2. Have a topic indicating freemium access
        freemium_challenges = []
        all_challenges = Challenges.query.filter(Challenges.state != "locked").all()
        
        for challenge in all_challenges:
            if challenge.get_subscription_required() == "freemium":
                freemium_challenges.append(challenge.id)
        
        chal_q = chal_q.filter(
            and_(Challenges.id.in_(freemium_challenges), Challenges.state != "locked")
        )
    elif sub == "premium":
        # For premium users, get challenges that are freemium OR premium
        accessible_challenges = []
        all_challenges = Challenges.query.filter(Challenges.state != "locked").all()
        
        for challenge in all_challenges:
            subscription_req = challenge.get_subscription_required()
            if subscription_req in ["freemium", "premium"]:
                accessible_challenges.append(challenge.id)
        
        chal_q = chal_q.filter(
            and_(Challenges.id.in_(accessible_challenges), Challenges.state != "locked")
        )
    elif sub == "all-in":
        accessible_challenges = []
        all_challenges = (
            Challenges.query
            .options(joinedload(Challenges.topics))
            .filter(and_(Challenges.state != "hidden", Challenges.state != "locked"))
            .all()
        )
        
        for challenge in all_challenges:
            subscription_req = challenge.get_subscription_required()
            if subscription_req in ["freemium", "premium", "all-in"]:
                accessible_challenges.append(challenge.id)
        
        chal_q = chal_q.filter(
            and_(
                Challenges.id.in_(accessible_challenges),
                Challenges.state != "hidden",
                Challenges.state != "locked"
            )
        )
    elif sub == "beta":
        # Test users can see everything (for testing purposes)
        accessible_challenges = []
        all_challenges = (
            Challenges.query
            .options(joinedload(Challenges.topics))
            .filter(and_(Challenges.state != "hidden", Challenges.state != "locked"))
            .all()
        )
        
        for challenge in all_challenges:
            subscription_req = challenge.get_subscription_required()
            # Test users see freemium, premium, all-in, AND beta challenges
            if subscription_req == "beta":
                accessible_challenges.append(challenge.id)
        
        chal_q = chal_q.filter(
            and_(
                Challenges.id.in_(accessible_challenges),
                Challenges.state != "hidden",
                Challenges.state != "locked"
            )
        )
    
    chal_q = (
        chal_q.filter_by(**query_args)
        .filter(*filters)
        .order_by(Challenges.value, Challenges.id)
    )

    tag_schema = TagSchema(view="user", many=True)

    results = []
    for c in chal_q:
        ct = Challenge(
            id=c.id,
            type=c.type,
            name=c.name,
            value=c.value,
            category=c.category,
            requirements=c.requirements,
            tags=tag_schema.dump(c.tags).data,
        )
        results.append(ct)
    return results
