from fastapi import HTTPException, status

username_taken = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST, detail="Username taken"
)


email_taken = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST, detail="Email taken"
)

inactive_user = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST, detail="User is Inactive. Please contact admin"
)

email_not_verified = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Please verify your email address",
)

failed_to_create_user = HTTPException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail="Could not create user account, try again later",
)

incorrect_usrnm_passwd = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect Username or Password"
)

bad_request = HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

invalid_token = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
)

not_found = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND, detail="Record not found"
)

# A standard
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

unexpected_error = HTTPException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error"
)

short_password = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST, detail="Weak Password"
)

user_disabled = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail="User disabled"
)

insufficaint_premissions = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN, detail="Insuffieciant Permissions"
)
