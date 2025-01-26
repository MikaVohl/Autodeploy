# Simple Deploy App with Frontend and Backend

This repository contains a simple Flask application with a frontend and backend. The app demonstrates basic deployment functionality and showcases interaction between a frontend and a REST API. Clicking a button on the frontend triggers a REST API call to fetch and display a "Hello, World!" message.

---

## Features

- **Frontend**: A simple HTML page with a button that fetches a message from the backend.
- **Backend**: A Flask server with an API endpoint (`/api/message`) that returns the "Hello, World!" message.

---

## How to Run the App

### 1. Clone the Repository

Clone the repository to your local machine:

```bash
git clone https://github.com/Arvo-AI/hello_world.git
```

---

### 2. Set Up a Virtual Environment

#### **On Windows**

1. Create a virtual environment:

   ```bash
   python -m venv venv
   ```

2. Activate the virtual environment:
   ```bash
   venv\Scripts\activate
   ```

#### **On macOS/Linux**

1. Create a virtual environment:

   ```bash
   python3 -m venv venv
   ```

2. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

---

### 3. Install Dependencies

Install the required Python packages:

```bash
pip install -r app/requirements.txt
```

---

### 4. Run the Flask App

Navigate to the `app` directory and run the app:

```bash
cd app
python app.py
```

---

### 5. Access the App

- Open your browser and navigate to:
  ```
  http://127.0.0.1:5000
  ```
- Click the button on the page to see the "Hello, World!" message fetched from the backend.
