🔐 Intelligent Login Security System

An login security system that detects suspicious login attempts using Machine Learning anomaly detection techniques.

📌 Overview

This project enhances traditional authentication systems by integrating Anomaly Detection to identify unusual login behavior.

Instead of only verifying username and password, the system analyzes login patterns such as:

IP Address

Login Time

Location

Device Information

If a login attempt deviates from normal behavior, it is flagged as suspicious.

🚀 Features

✅ Secure user authentication

✅ Anomaly Detection using Isolation Forest

✅ Real-time suspicious login detection

✅ Backend built with Flask

✅ Machine Learning using Scikit-learn

✅ Clean and modular project structure

🛠️ Tech Stack

Backend: Python, Flask

Machine Learning: Scikit-learn (Isolation Forest)

Database: SQLite / PostgreSQL

Authentication: JWT (JSON Web Tokens)

Other Libraries: Pandas, NumPy

🤖 Machine Learning Model

We use Isolation Forest, an unsupervised learning algorithm, to detect anomalies.

Why Isolation Forest?

Works well for anomaly detection

Efficient for large datasets

Does not require labeled attack data

The model is trained on normal login behavior and detects unusual patterns as anomalies.

📂 Project Structure
project/
│── backend/
│   ├── app.py
│   ├── models.py
│   ├── auth.py
│   └── anomaly_detection.py
│
│── database/
│── requirements.txt
│── README.md
⚙️ Installation & Setup
1️⃣ Clone the Repository
git clone https://github.com/your-username/intelligent-login-security.git
cd intelligent-login-security
2️⃣ Create Virtual Environment
python -m venv venv
venv\Scripts\activate   # Windows
3️⃣ Install Dependencies
pip install -r requirements.txt
4️⃣ Run the Application
python app.py
📊 How It Works

User logs in with credentials

System verifies authentication

Login features are passed to ML model

Model predicts:

Normal Login

Suspicious Login (Anomaly)

Suspicious attempts are flagged for review

🎯 Future Improvements

Multi-Factor Authentication (MFA)

Real-time dashboard for monitoring

Email/SMS alert system

Deep learning-based anomaly detection

📌 Conclusion

This project demonstrates how Machine Learning can be integrated into authentication systems to enhance cybersecurity by detecting suspicious login behavior in real time.
