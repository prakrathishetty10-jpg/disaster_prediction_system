# 🌍 Earthquake Prediction System

A Python-based **earthquake risk assessment system** that integrates earthquake data from the **USGS (United States Geological Survey)** and evaluates earthquake risk based on geographic coordinates.

The system allows users to enter latitude and longitude coordinates, retrieve recent earthquake information, analyze earthquake magnitude and proximity, calculate a risk level, and maintain prediction history.

## 🚀 Features

* 🌐 **Real-Time USGS Data Integration**

  * Retrieves recent earthquake information from the USGS API.
  * Automatically refreshes earthquake data periodically.

* 📍 **Coordinate-Based Risk Assessment**

  * Accepts latitude and longitude as input.
  * Validates geographic coordinates before processing.

* 📊 **Earthquake Risk Analysis**

  * Analyzes nearby earthquake activity.
  * Considers earthquake magnitude and distance.
  * Uses weighted calculations based on earthquake proximity.

* 🗺️ **Location Detection**

  * Uses reverse geocoding to convert coordinates into human-readable location information.

* 🔐 **User Authentication**

  * User registration and login functionality.
  * Password recovery support.

* 📜 **Prediction History**

  * Stores previous earthquake risk assessments.
  * Maintains user-specific prediction records.

* 🔊 **Risk-Level Alerts**

  * Provides different alerts based on the calculated risk level.

## 🛠️ Technologies Used

* **Python**
* **MySQL / MariaDB**
* **USGS Earthquake API**
* **Nominatim Reverse Geocoding**
* **Haversine Formula**
* **HTML / CSS**
* **JavaScript**

## 📋 Risk Levels

| Risk Level | Magnitude Range | Description                  |
| ---------- | --------------: | ---------------------------- |
| Very Low   |           ≤ 2.0 | No significant threat        |
| Low        |       2.1 – 3.9 | Minor shaking possible       |
| Moderate   |       4.0 – 4.9 | Noticeable shaking           |
| High       |       5.0 – 5.9 | Significant damage possible  |
| Very High  |       6.0 – 6.9 | Major damage likely          |
| Extreme    |           ≥ 7.0 | Catastrophic damage possible |

> **Note:** These risk categories are project-defined assessment levels and should not be interpreted as official earthquake warnings.

## ⚙️ How It Works

```text
User
  │
  ▼
Enter Latitude & Longitude
  │
  ▼
Validate Coordinates
  │
  ▼
Fetch Recent Earthquake Data from USGS
  │
  ▼
Calculate Distance using Haversine Formula
  │
  ▼
Analyze Magnitude & Proximity
  │
  ▼
Calculate Risk Level
  │
  ▼
Display Risk Assessment
  │
  ▼
Store Prediction History
```

## 💻 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/prakrathishetty10-jpg/disaster_prediction_system.git
cd disaster_prediction_system
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure the Database

Install **MySQL/MariaDB** and create the required database and tables.

The application uses:

* `users_details` — stores user account information.
* `eq_history` — stores earthquake prediction history.

### 4. Run the Application

```bash
python test1.py
```

Follow the application's login/registration flow and provide geographic coordinates to perform an earthquake risk assessment.

## 🗄️ Database Schema

### Users Table

```sql
CREATE TABLE users_details (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255),
    username VARCHAR(255) UNIQUE,
    pass VARCHAR(255)
);
```

### Earthquake History Table

```sql
CREATE TABLE eq_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    magnitude DECIMAL(4,2),
    location TEXT,
    status VARCHAR(100),
    user_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 📡 Data Sources & APIs

### USGS Earthquake API

The application retrieves recent earthquake information from the USGS service and uses the available earthquake data for risk analysis.

### Nominatim

Nominatim is used for reverse geocoding to convert latitude and longitude coordinates into readable location information.

## 🔬 Technical Implementation

### Haversine Formula

The system uses the **Haversine formula** to calculate the distance between geographic coordinates.

### Weighted Risk Analysis

Earthquake magnitude and proximity are considered when calculating the risk level. Earthquakes closer to the selected coordinates can have a greater influence on the assessment.

### Coordinate Validation

* Latitude: `-90` to `90`
* Longitude: `-180` to `180`

Invalid coordinates are rejected with appropriate validation feedback.

### Automatic Data Refresh

The system retrieves recent earthquake data periodically and also supports manual data refresh.

## 📁 Project Structure

```text
disaster_prediction_system/
│
├── admin.py
├── test1.py
├── song.py
├── requirements.txt
├── data.csv
├── login.spec
│
├── dashboard_bg.png
├── dashboard_bg_1.png
├── dashboard_bg_2.png
├── login_bg.png
├── signup_bg.png
├── logo.png
├── robot.png
├── danger.png
├── warning.png
├── success.png
├── welcome.jpg
│
├── danger.mp3
├── warning.mp3
├── success.mp3
│
├── README.md
└── .gitignore
```

## 📌 Project Highlights

* Real-time earthquake data integration
* Geographic coordinate-based risk assessment
* Distance calculation using the Haversine formula
* Weighted earthquake risk analysis
* Reverse geocoding
* User authentication
* Prediction history
* Risk-level classification
* Automated earthquake data refresh

## 🔮 Future Enhancements

* Machine learning-based earthquake risk models
* Interactive map visualization
* Historical earthquake graphs and analytics
* Email/SMS emergency notifications
* Cloud deployment
* Docker containerization
* CI/CD pipeline using GitHub Actions
* AWS-based deployment and monitoring

## ⚠️ Disclaimer

This project provides an **earthquake risk assessment** based on available earthquake data and project-defined risk calculations.

It is **not a guaranteed earthquake prediction system** and should not be used as the sole source for emergency or safety decisions.

Always follow official earthquake warnings and emergency guidelines.

## 👩‍💻 Author

**Prakrithi Shetty**

GitHub:
https://github.com/prakrathishetty10-jpg
