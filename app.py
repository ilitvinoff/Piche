from flask import Flask, jsonify, request
from flask_restful import Resource, Api
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from flask_jwt_extended.exceptions import NoAuthorizationError, InvalidHeaderError, WrongTokenError, RevokedTokenError, FreshTokenRequired, CSRFError
from accounts import (
    authenticate, create_account, deposit, transfer, withdraw,
    AccountNotFoundError, InsufficientFundsError, InvalidDataError, AuthenticationError
)
import logging
from datetime import datetime


app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "super-secret-key"  # Should be an environment variable in production

  
class CustomApi(Api):
    def handle_error(self, e):
        if isinstance(e, InvalidDataError):
            error_logger.error(f"Invalid data: {e}")
            return jsonify({"error": "Invalid request data"}), 400
        
        if isinstance(e, InsufficientFundsError):
            error_logger.error(f"Insufficient funds: {e}")
            return jsonify({"error": "Insufficient funds"}), 400
        
        if isinstance(e, AccountNotFoundError):
            error_logger.error(f"Account not found: {e}")
            return jsonify({"error": "Account not found"}), 404

        if isinstance(e, AuthenticationError):
            error_logger.error(f"Authentication error: {e}")
            return jsonify({"error": "Authentication failed"}), 401
        
        if isinstance(e, (NoAuthorizationError, InvalidHeaderError, WrongTokenError, RevokedTokenError, FreshTokenRequired, CSRFError)):
            error_logger.error(f"JWT error: {e}")
            return jsonify({"error": "Missing or invalid Authorization Header"}), 401

        error_logger.error(f"Unexpected error: {e}")
        if hasattr(e, 'code') and e.code in (400, 401, 403, 404, 500):
            return super().handle_error(e)
        
        return jsonify({"error": "An unexpected error occurred"}), 500


api = CustomApi(app)
jwt = JWTManager(app)


# Configure transaction logger
transaction_logger = logging.getLogger("transaction_logger")
transaction_logger.setLevel(logging.INFO)
file_handler = logging.FileHandler("transactions.log")
file_handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
if not transaction_logger.hasHandlers():
    transaction_logger.addHandler(file_handler)


# Configure error logger
error_logger = logging.getLogger("error_logger")
error_logger.setLevel(logging.ERROR)
error_file_handler = logging.FileHandler("errors.log")
error_file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
if not error_logger.hasHandlers():
    error_logger.addHandler(error_file_handler)


class LoginResource(Resource):
    def post(self):
        try:
            user = authenticate(request.get_json())
            access_token = create_access_token(identity=user.name)
            return {"access_token": access_token}, 200
        except InvalidDataError as e:
            return {"error": "Invalid credentials"}, 401
        

class CreateAccountResource(Resource):
    def post(self):
        return create_account(request.get_json()), 201


class DepositResource(Resource):
    @jwt_required()
    def post(self):
        data = request.get_json()
        result = deposit(data)
        transaction_logger.info(f"DEPOSIT account_id={data.get('account_id')} amount={data.get('amount')}")
        return result, 200


class WithdrawResource(Resource):
    @jwt_required()
    def post(self):
        data = request.get_json()
        result = withdraw(data)
        transaction_logger.info(f"WITHDRAW account_id={data.get('account_id')} amount={data.get('amount')}")
        return result, 200


class TransferResource(Resource):
    @jwt_required()
    def post(self):
        data = request.get_json()
        result = transfer(data)
        transaction_logger.info(f"TRANSFER from_account_id={data.get('from_account_id')} to_account_id={data.get('to_account_id')} amount={data.get('amount')}")
        return result, 200


api.add_resource(LoginResource, '/login')
api.add_resource(CreateAccountResource, '/create_account')
api.add_resource(DepositResource, '/deposit')
api.add_resource(WithdrawResource, '/withdraw')
api.add_resource(TransferResource, '/transfer')