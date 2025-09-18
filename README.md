# Minimal Flask Application

This is a minimal Flask application that includes a healthcheck endpoint.

## Project Structure

```
minimal-flask-app
├── app.py
├── requirements.txt
└── README.md
```

## Installation

1. Clone the repository or download the project files.
2. Navigate to the project directory.
3. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   ```
4. Activate the virtual environment:
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```
     source venv/bin/activate
     ```
5. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Running the Application

To run the application, execute the following command:

```
python app.py
```

The application will start, and you can access it at `http://127.0.0.1:5000`.

## Healthcheck Endpoint

- **GET /ping**: Returns a JSON response with the status of the application.
  - Response:
    ```json
    {
      "status": "ok"
    }
    ```