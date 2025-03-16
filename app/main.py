from datetime import datetime, timedelta
import json
import secrets
import requests
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.security import HTTPBasic, HTTPBasicCredentials, OAuth2PasswordBearer

from sqlalchemy.ext.asyncio import AsyncSession



from app.api.api_v1.main import api_router
from app.api.deps import get_session
from app.core.auth import generate_jwt
from app.core.config import settings
from app.crud.user import create_social_user, create_social_user_id_and_provider, get_user_by_social_id, get_user_by_username


app = FastAPI(
    title=f"{settings.PROJECT_TITLE}",
    description=f"{settings.PROJECT_DESCRIPTION}",
    version=f"{settings.PROJECT_VERSION}",
    contact={
        "email": f"{settings.PROJECT_DEV_EMAIL}",
    },
    license_info={
        "name": f"{settings.PROJECT_LICENSE_INFO}",
    },
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)









security = HTTPBasic()


def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(
        credentials.username, settings.DOCS_USERNAME
    )
    correct_password = secrets.compare_digest(
        credentials.password, settings.DOCS_PASSWORD
    )
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@app.get("/docs")
async def get_documentation(username: str = Depends(get_current_username)):  # noqa: ARG001
    return get_swagger_ui_html(
        openapi_url="/openapi.json", title=f"{settings.PROJECT_TITLE}"
    )


@app.get("/openapi.json")
async def openapi(username: str = Depends(get_current_username)):  # noqa: ARG001
    return get_openapi(
        title=f"{settings.PROJECT_TITLE}",
        description=f"{settings.PROJECT_DESCRIPTION}",
        version=f"{settings.PROJECT_VERSION}",
        contact={
            "email": f"{settings.PROJECT_DEV_EMAIL}",
        },
        license_info={
            "name": f"{settings.PROJECT_LICENSE_INFO}",
        },
        routes=app.routes,
    )



origins = [
    "http://localhost:8000",
    "http://localhost:5173",
    "http://localhost:3002",
    "http://192.168.0.101:5173",
    "http://192.168.0.104:5173",
    "http://192.168.0.108:5173",
    "https://192.168.118.133:5173",
    "https://192.168.72.133:5173",
    "https://192.168.206.133:5173",
    "https://app.getrealfund.com",
    "https://www.app.getrealfund.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/")
async def root():
    return "Welcome to our System"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Replace these with your own values from the Google Developer Console
GOOGLE_CLIENT_ID = settings.CLIENT_ID
GOOGLE_CLIENT_SECRET = settings.CLIENT_SECRET
GOOGLE_REDIRECT_URI = settings.REDIRECT_URI


@app.get("/login/google")
async def login_google():
    return {
        "url": f"https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={GOOGLE_CLIENT_ID}&redirect_uri={GOOGLE_REDIRECT_URI}&scope=openid%20profile%20email&access_type=offline"
    }


@app.get("/auth/callback")
async def auth_google(code: str, db: AsyncSession = Depends(get_session)):
    token_url = "https://accounts.google.com/o/oauth2/token"
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    response = requests.post(token_url, data=data)
    access_token = response.json().get("access_token")
    user_info = requests.get(
        "https://www.googleapis.com/oauth2/v1/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    user_info = user_info.json()
    print("user_info", user_info)
    #Check if user already exists
    user = await get_user_by_social_id(db, social_id=user_info['id'], provider="google")

    if not user:
        user_exists_locally = await get_user_by_username(db,user_info['email'])

        if user_exists_locally:
            await create_social_user_id_and_provider(db, user_info, "google")

        else:
            user = await create_social_user(db, user_info, "google")

    # print("user is ",user)
    # if not user:
    #     # Create a new user if not found
    #     user = await create_social_user(db, user_info, "google")

    jwt_client_access_timedelta = timedelta(
        minutes=settings.CRYPTO_JWT_ACESS_TIMEDELTA_MINUTES
    )
    data_to_be_encoded = {
        "email": user.username,
        "type": "acess_token",
    }

    new_jwt_access = generate_jwt(
        data={"sub": json.dumps(data_to_be_encoded)},
        expires_delta=jwt_client_access_timedelta,
    )

    user.last_login = datetime.now()

    print("user.last_login", user.last_login)

    await db.commit()

    return {
        "access_token": new_jwt_access,
        "token_type": "bearer",
        "is_superadmin": user.is_super_admin,
    }



app.include_router(api_router, prefix="/api/v1")
