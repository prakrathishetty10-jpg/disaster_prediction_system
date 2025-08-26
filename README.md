# Earthquake Prediction System

A real-time earthquake risk prediction system that integrates with USGS (United States Geological Survey) data to provide accurate earthquake predictions based on geographic coordinates.

## Features

- **Real-time USGS Data Integration**: Automatically fetches earthquake data from USGS API every 10 minutes
- **Coordinate-based Prediction**: Enter latitude and longitude to get earthquake risk assessment
- **Advanced Risk Analysis**: Uses weighted algorithms based on nearby earthquake data
- **Location Detection**: Automatic reverse geocoding to identify location names
- **User Authentication**: Secure login and registration system
- **Password Recovery**: Forgot password functionality
- **Prediction History**: Track all your earthquake predictions
- **Audio Alerts**: Different sound alerts based on risk level

## Installation

1. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Database Setup**:
   - Install MySQL/MariaDB
   - Create a database named `alpha`
   - Create the required tables (see Database Schema below)

3. **Run the Application**:
   ```bash
   python test1.py
   ```

## Database Schema

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

## Usage

### 1. Login/Registration
- Use the login page to access the system
- Register a new account if you don't have one
- Use "Forgot Password" to reset your password

### 2. Earthquake Prediction
- Navigate to "Earthquake Prediction" from the sidebar
- Enter latitude and longitude coordinates
- The system will automatically:
  - Fetch real-time USGS earthquake data
  - Calculate risk based on nearby earthquakes
  - Determine location name using reverse geocoding
  - Provide risk assessment

### 3. Risk Levels
- **Very Low Risk (≤2.0)**: No significant threat
- **Low Risk (2.1-3.9)**: Minor shaking possible
- **Moderate Risk (4.0-4.9)**: Noticeable shaking
- **High Risk (5.0-5.9)**: Significant damage possible
- **Very High Risk (6.0-6.9)**: Major damage likely
- **Extreme Risk (≥7.0)**: Catastrophic damage possible

### 4. USGS Data
- Data is automatically refreshed every 10 minutes
- Use "Refresh USGS Data" button for manual refresh
- View data status and last update time

## Technical Details

### USGS API Integration
- Fetches earthquake data from the last 7 days
- Uses Haversine formula for accurate distance calculations
- Weighted magnitude calculation based on proximity
- Automatic error handling and retry mechanisms

### Coordinate Validation
- Latitude: -90 to 90 degrees
- Longitude: -180 to 180 degrees
- Automatic validation and error messages

### Geocoding
- Uses Nominatim service for reverse geocoding
- Converts coordinates to human-readable location names
- Fallback handling for geocoding failures

## Troubleshooting

### Common Issues

1. **Database Connection Error**:
   - Ensure MySQL is running
   - Check database credentials in the code
   - Verify database and tables exist

2. **USGS Data Not Loading**:
   - Check internet connection
   - Verify USGS API accessibility
   - Use manual refresh button

3. **Geocoding Errors**:
   - Check internet connection
   - Some coordinates may not have location names
   - System will fallback to coordinate display

### Performance Tips

- The system fetches data every 10 minutes to balance accuracy and performance
- Large coordinate areas may take longer to process
- Keep the application running for continuous data updates

## Contributing

Feel free to contribute to this project by:
- Reporting bugs
- Suggesting new features
- Improving the prediction algorithms
- Enhancing the user interface

## License

This project is open source and available under the MIT License.

## Disclaimer

This system provides risk assessments based on available data and should not be used as the sole source for emergency decisions. Always follow official emergency guidelines and warnings.
