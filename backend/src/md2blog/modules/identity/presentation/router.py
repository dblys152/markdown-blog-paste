from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from md2blog.modules.identity.application.factory.signup import SignUpCommandFactory
from md2blog.modules.identity.application.port.inbound.models import TokenResponse, UserResponse
from md2blog.modules.identity.application.port.inbound.signup import SignUpRequest, SignUpUseCase
from md2blog.modules.identity.application.service.signup import EmailAlreadyExistsError, SignUp
from md2blog.modules.identity.infrastructure.passwords import Argon2PasswordHasher
from md2blog.modules.identity.infrastructure.repositories import SqlAlchemyUserRepository
from md2blog.modules.identity.infrastructure.tokens import JwtAccessTokenIssuer
from md2blog.settings import get_settings
from md2blog.shared.infrastructure.database import get_session

router = APIRouter(prefix="/auth", tags=["auth"])


def get_signup_dependencies(
    session: AsyncSession = Depends(get_session),
) -> tuple[SignUpCommandFactory, SignUpUseCase]:
    settings = get_settings()
    users = SqlAlchemyUserRepository(session)
    return (
        SignUpCommandFactory(users=users, password_hasher=Argon2PasswordHasher()),
        SignUp(
            users=users,
            token_issuer=JwtAccessTokenIssuer(
            settings.jwt_secret_key.get_secret_value(),
            timedelta(minutes=settings.access_token_ttl_minutes),
        ),
        ),
    )


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    request: SignUpRequest,
    dependencies: tuple[SignUpCommandFactory, SignUpUseCase] = Depends(get_signup_dependencies),
) -> TokenResponse:
    command_factory, use_case = dependencies
    try:
        command = await command_factory.create(request)
        result = await use_case.execute(command)
    except (EmailAlreadyExistsError, IntegrityError) as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="email already exists",
        ) from error

    return TokenResponse(
        access_token=result.access_token,
        user=UserResponse(
            id=str(result.user.id),
            email=result.user.email.value,
            display_name=result.user.display_name.value,
        ),
    )
