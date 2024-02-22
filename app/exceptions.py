from fastapi import HTTPException, status

# Some standard exceptions

API_400_BAD_REQUEST_EXCEPTION = HTTPException(
    status_code=400,
    detail="Bad Request",
)

API_401_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could Not Validate Credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

API_404_NOT_FOUND_EXCEPTION = HTTPException(
    status_code=404,
    detail="Not Found",
)

API_409_USERNAME_CONFLICT_EXCEPTION = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Username Already Exists"
)

API_500_SIGNATURE_EXCEPTION = HTTPException(
    status_code=500,
    detail="Internal Server Error",
)

