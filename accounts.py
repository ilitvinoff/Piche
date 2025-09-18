from pydantic import BaseModel, PositiveFloat, ValidationError, field_validator, model_validator

# In-memory storage for bank accounts
accounts_by_name = {}
accounts = {}
next_account_id = 1

class AccountNotFoundError(Exception):
    pass

class InsufficientFundsError(Exception):
    pass

class InvalidDataError(Exception):
    pass

class AuthenticationError(Exception):
    pass


class AccountModel(BaseModel):
    id: int
    name: str
    balance: float
    password: str


    def __init__(self, **data):
        super().__init__(**data)

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Name must be a non-empty string")
        return v

    @field_validator("password")
    @classmethod
    def password_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Password must be a non-empty string")
        return v

    @field_validator("balance")
    @classmethod
    def balance_must_be_non_negative(cls, v):
        if v < 0:
            raise ValueError("Balance cannot be negative")
        return v

def authenticate(raw_data):
    account_id = accounts_by_name.get(raw_data.get("name"))
    password = raw_data.get("password")
    if account_id is None or password is None:
        raise AuthenticationError("Authentication failed: account_id and password are required")
    account = accounts.get(account_id)
    if not account or account.password != password:
        raise AuthenticationError("Authentication failed: invalid account_id or password")
    return account

def create_account(raw_data):
    global next_account_id

    try:
        raw_data["id"] = next_account_id
        account = AccountModel.model_validate(raw_data)
        if account.name in accounts_by_name:
            raise InvalidDataError(f"Account creation failed: name '{account.name}' already exists")

    except ValidationError as e:
        raise InvalidDataError(f"Create account failed: {e.errors()}")

    accounts[next_account_id] = account
    accounts_by_name[account.name] = next_account_id
    next_account_id += 1

    account_data = account.model_dump()
    account_data.pop("password", None)
    return account_data

def _get_account(account_id):
    account = accounts.get(account_id)
    
    if not account:
        raise AccountNotFoundError(f"Account `id={account_id}` not found")

    return account

def _update_account_balance(account, new_balance):
    account.balance = new_balance
    accounts[account.id] = account
    return account


class DepositWithdrawRequest(BaseModel):
    account_id: int
    amount: PositiveFloat

def deposit(raw_data):
    # Must be wrapped in a transaction in a real-world scenario
    try:
        data = DepositWithdrawRequest.model_validate(raw_data)
        account = _get_account(data.account_id)
        return _update_account_balance(account, account.balance + data.amount).model_dump()
    except ValidationError as e:
        raise InvalidDataError(f"Deposit failed: {e.errors()}")
    except AccountNotFoundError as e:
        raise AccountNotFoundError(f"Deposit failed: {e}")
    
def withdraw(raw_data):
    # Must be wrapped in a transaction in a real-world scenario
    try:
        data = DepositWithdrawRequest.model_validate(raw_data)
        account = _get_account(data.account_id)
        if account.balance < data.amount:
            raise InsufficientFundsError(f"Withdraw failed `data={data}`: insufficient funds")
        return _update_account_balance(account, account.balance - data.amount).model_dump()
    except ValidationError as e:
        raise InvalidDataError(f"Withdraw failed: {e.errors()}")
    except AccountNotFoundError as e:
        raise AccountNotFoundError(f"Withdraw failed: {e}")



class TransferRequest(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: PositiveFloat

    @model_validator(mode='after')
    def check_accounts_not_same(self):
        if self.from_account_id == self.to_account_id:
            raise InvalidDataError("from_account_id and to_account_id cannot be the same")
        return self
    
def transfer(raw_data):
    # Must be wrapped in a transaction in a real-world scenario

    try:
        data = TransferRequest.model_validate(raw_data)
        from_account = _get_account(data.from_account_id)
        to_account = _get_account(data.to_account_id)
    except ValidationError as e:
        raise InvalidDataError(f"Transfer from `id={raw_data.get("from_account_id")}` to `id={raw_data.get("to_account_id")}` failed: {e.errors()}")
    except AccountNotFoundError as e:
        raise AccountNotFoundError(f"Transfer from `id={data.from_account_id}` to `id={data.to_account_id}` failed: {e}")

    if from_account.balance < data.amount:
        raise InsufficientFundsError(f"Transfer from `id={from_account.id}` to `id={to_account.id}` failed: insufficient funds")

    from_account.balance -= data.amount
    to_account.balance += data.amount
    return from_account.model_dump(), to_account.model_dump()
