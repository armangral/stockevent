from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.invitation import Invitation
from app.models.invitation_password import InvitationPassword


async def get_valid_invitation_by_token(
    db: AsyncSession, token: str
) -> Invitation | None:
    result = await db.execute(select(Invitation).where(Invitation.token == token))
    invitation = result.scalars().first()
    if invitation and not invitation.is_expired:
        return invitation
    return None

async def get_valid_password_invitation_by_token(
    db: AsyncSession, token: str
) -> InvitationPassword | None:
    result = await db.execute(
        select(InvitationPassword).where(InvitationPassword.token == token)
    )
    invitation = result.scalars().first()
    if invitation and not invitation.is_expired:
        return invitation
    return None
