from fastapi import HTTPException, status

API_400_BAD_REQUEST_EXCEPTION = HTTPException(
    status_code=400,
    detail="bad request",
)

API_401_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

API_404_NOT_FOUND_EXCEPTION = HTTPException(
    status_code=404,
    detail="not found",
)

API_409_USERNAME_CONFLICT_EXCEPTION = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="username already exists"
)

API_500_SIGNATURE_EXCEPTION = HTTPException(
    status_code=500,
    detail="server error",
)

