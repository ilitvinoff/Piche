from flask import Flask, jsonify, request
from flask_restful import Resource, Api
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from accounts import (
    authenticate, create_account, deposit, transfer,
    AccountNotFoundError, InsufficientFundsError, InvalidDataError, withdraw
)
import logging
from datetime import datetime


app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "super-secret-key"  # Should be an environment variable in production


api = Api(app)
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


@app.errorhandler(AccountNotFoundError)
def handle_account_not_found(error):
    error_logger.error(f"Account not found: {error}")
    return jsonify({"error": "Account not found"}), 404


@app.errorhandler(InsufficientFundsError)
def handle_insufficient_funds(error):
    error_logger.error(f"Insufficient funds: {error}")
    return jsonify({"error": "Insufficient funds"}), 400


@app.errorhandler(InvalidDataError)
def handle_invalid_account_data(error):
    error_logger.error(f"Invalid data: {error}")
    return jsonify({"error": "Invalid request data"}), 400


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    error_logger.error(f"Unexpected error: {error}")
    return jsonify({"error": "An internal error occurred"}), 500


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


if __name__ == '__main__':
    app.run(debug=True)