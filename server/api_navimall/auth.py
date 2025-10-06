from fastapi import Header, Depends, HTTPException
from api_navimall.config import API_KEYS


from fastapi import Header, HTTPException
from api_navimall.config import API_KEYS


def verify_api_key(x_api_key: str = Header(...)):
    """
    Verifies the provided API key against the stored keys.
    Raises HTTPException if the key is invalid.
    """
    for user, info in API_KEYS.items():
        if info["key"] == x_api_key:
            return {"user": user, "role": info["role"]}
    raise HTTPException(status_code=401, detail="Invalid API Key")


def verify_write_rights(user_info=Depends(verify_api_key)):
    """
    Verifies that the user has write privilege
    ONly users with role='write' or better can read and write.
    Vérifie que l'utilisateur a des droits d'écriture.
    """
    if user_info["role"] != "write":
        raise HTTPException(status_code=403, detail="Permission denied: read-only user")
    return user_info
