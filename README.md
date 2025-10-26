# 🏓 Training Hall Booking App

A lightweight **Flask web application** for managing table tennis hall bookings, match days, and live occupancy tracking — optimized for Raspberry Pi deployment.

---

## 🚀 Features
- Player and partner booking system with conflict prevention  
- Admin panel to configure **match day**, **extra tables**, and **second match** slots  
- Real-time occupancy updates  
- Check-in and check-out tracking  
- Automatic daily cleanup of old bookings  
- Responsive front-end interface  

---

## 🧰 Technologies Used
- **Backend:** Flask (Python 3.13), Flask-SQLAlchemy  
- **Frontend:** HTML, JavaScript, Bootstrap  
- **Database:** SQLite  
- **Scheduler:** APScheduler (daily cleanup task)  
- **Environment Management:** python-dotenv  
- **Deployment:** Raspberry Pi–friendly lightweight server  

---

## ⚙️ Setup Instructions

1. **Clone this repository**
   ```bash
   git clone https://github.com/clf94/training_hall_booking_app.git
   cd training-hall-booking```

2. **Create a virtual environment and install dependencies
```python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt```

3. **Set up environment variables
```FLASK_SECRET=your_secret_key
ADMIN_PASSWORD=your_admin_password
```

4. **Run the application
```python app.py

```
Then visit ```http://localhost:5009```
