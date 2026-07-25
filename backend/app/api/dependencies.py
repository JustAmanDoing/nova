import secrets
from typing import Annotated

from fastapi import Header, HTTPException

LOCAL_ACTION_HEADER = "X-Nova-Intent"
LOCAL_ACTION_VALUE = "local-user-action"


def require_local_action(
    intent: Annotated[
        str | None,
        Header(alias=LOCAL_ACTION_HEADER),
    ] = None,
) -> None:
    if intent is None or not secrets.compare_digest(intent, LOCAL_ACTION_VALUE):
        raise HTTPException(
            status_code=403,
            detail="This change requires a request from Nova's local interface.",
        )
