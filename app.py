from flask import Flask, jsonify, request
from flask_restful import Resource, Api
from accounts import (
    create_account, deposit, transfer,
    AccountNotFoundError, InsufficientFundsError, InvalidDataError, withdraw
)

app = Flask(__name__)
api = Api(app)

@app.errorhandler(AccountNotFoundError)
def handle_account_not_found(error):
    return jsonify({"error": str(error)}), 404

@app.errorhandler(InsufficientFundsError)
def handle_insufficient_funds(error):
    return jsonify({"error": str(error)}), 400

@app.errorhandler(InvalidDataError)
def handle_invalid_account_data(error):
    return jsonify({"error": str(error)}), 400


class CreateAccountResource(Resource):
    def post(self):
        return create_account(request.get_json()), 201

class DepositResource(Resource):
    def post(self):
        return deposit(request.get_json()), 200


class WithdrawResource(Resource):
    def post(self):
        return withdraw(request.get_json()), 200

class TransferResource(Resource):
    def post(self):
        return transfer(request.get_json()), 200

api.add_resource(CreateAccountResource, '/create_account')
api.add_resource(DepositResource, '/deposit')
api.add_resource(WithdrawResource, '/withdraw')
api.add_resource(TransferResource, '/transfer')

if __name__ == '__main__':
    app.run(debug=True)