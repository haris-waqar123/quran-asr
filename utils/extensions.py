import firebase_admin
from firebase_admin import auth
from flask import abort



def verify_token(token):
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except auth.InvalidIdTokenError:
        abort(401, description="Invalid or expired token")
    except Exception as e:
        abort(401, description=f"Token verification failed: {str(e)}")