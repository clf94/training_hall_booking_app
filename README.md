# 🏓 Training Hall Booking App

A lightweight **Flask web application** for managing table tennis hall bookings, match days, and live occupancy tracking — optimized for Raspberry Pi deployment.
Includes **n8n webhook notifications** for automated alerts (e.g., via email, Telegram, or Slack)whenever a new booking is created.
---

## 🚀 Features

- 🎾 Player and partner booking system with **conflict prevention**
- 🧑‍💼 **Admin panel** to configure match days, extra tables, and second matches
- 📊 **Real-time occupancy tracking** with match-day adjustments
- 🕓 Check-in and check-out support
- 🧹 Automatic **daily cleanup** of old bookings (via APScheduler)
- 🔔 **Webhook notification** to n8n on each new booking
- 📱 Responsive and lightweight UI (perfect for Raspberry Pi touchscreen setups)

---

## 🧰 Technologies Used
- **Backend:** Flask (Python 3.13), Flask-SQLAlchemy  
- **Frontend:** HTML, JavaScript, Bootstrap  
- **Database:** SQLite  
- **Scheduler:** APScheduler (daily cleanup task)  
- **Notifications:** n8n webhook integration
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
WEB_HOOK_N8N_URL=https://your-n8n-domain.ngrok-free.dev/webhook-test/booking-created
```

4. **Run the application
```python app.py

```
Then visit ```http://localhost:5009```

🔔. **n8n Webhook Integration
```{
  "player": "Player 1",
  "partner": "Player 2",
  "day": "2025-10-27",
  "start": "10:00",
  "end": "11:00",
  "created_at": "2025-10-26T09:45:00+01:00"
}

```
