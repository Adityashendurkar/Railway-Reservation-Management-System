# 🚆 Railway Reservation Management System

Built from the ER Diagram with 5 entities:
**Passenger → (issue) → Ticket ← Train Detail ← (manage) ← Technical Supervisor**
**Passenger → (checks) → Train Detail**
**Ticket → (done/payment) → Payment**

---

## 📁 Project Structure

```
railway_project/
├── schema.sql              ← MySQL database schema + sample data
├── backend/
│   ├── app.py              ← Python Flask backend (all API routes)
│   └── requirements.txt    ← Python dependencies
└── frontend/
    └── index.html          ← Complete frontend (single HTML file)
```

---

## ⚙️ Setup Instructions (Step by Step)

### STEP 1 — Install MySQL
- Download MySQL: https://dev.mysql.com/downloads/installer/
- Remember your root username and password

### STEP 2 — Create the Database
Open MySQL Workbench or terminal and run:
```sql
source /path/to/railway_project/schema.sql
```
Or copy-paste the entire schema.sql content into MySQL Workbench and run it.

### STEP 3 — Install Python
- Download Python 3.10+: https://python.org/downloads
- Make sure to check "Add Python to PATH" during install

### STEP 4 — Install Backend Dependencies
Open terminal/command prompt:
```bash
cd railway_project/backend
pip install -r requirements.txt
```

### STEP 5 — Configure Database in app.py
Open `backend/app.py` and edit lines 18–23:
```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",        # ← your MySQL username
    "password": "YOUR_PW", # ← your MySQL password
    "database": "railway_db"
}
```

### STEP 6 — Start the Backend Server
```bash
cd railway_project/backend
python app.py
```
You should see: `Running on http://127.0.0.1:5000`

### STEP 7 — Open the Frontend
Simply open `frontend/index.html` in your browser.
That's it! No server needed for frontend.

---

## 🔑 Default Credentials

### Passenger (Register your own)
- Go to Login → Register tab → Create account

### Technical Supervisor (Admin)
- Email: `admin@railway.com`
- Password: `admin123`

---

## 🗺️ ER Diagram → Code Mapping

| ER Diagram Element | Code Implementation |
|---|---|
| **Passenger** entity | `passenger` table + `/api/passenger/*` routes |
| **Ticket** entity | `ticket` table + `/api/ticket/*` routes |
| **Train Detail** entity | `train_detail` table + `/api/trains/*` routes |
| **Payment** entity | `payment` table + `/api/payment/*` routes |
| **Technical Supervisor** entity | `technical_supervisor` table + `/api/supervisor/*` routes |
| **ISSUE** relationship | `POST /api/ticket/book` links Passenger → Ticket |
| **CHECKS** relationship | Passenger login verifies auth before booking any train |
| **DONE/PAYMENT** relationship | `PUT /api/payment/{id}/complete` marks payment as Done |
| **MANAGE** relationship | Supervisor CRUD on trains via `/api/supervisor/trains` |
| Passenger: phone_no (PK?) | Used as unique login identifier |
| Ticket: ticket_id (PK) | Auto-increment primary key |
| Payment: payment_id (PK) | Auto-increment primary key |

---

## 📡 API Endpoints Reference

### Passenger
| Method | URL | Description |
|---|---|---|
| POST | `/api/passenger/register` | Register new passenger |
| POST | `/api/passenger/login` | Login with phone + password |
| GET | `/api/passenger/{id}` | Get passenger info |

### Trains
| Method | URL | Description |
|---|---|---|
| GET | `/api/trains` | List all trains |
| GET | `/api/trains/search?source=X&destination=Y` | Search trains by route |
| GET | `/api/trains/{train_no}` | Get one train |

### Tickets
| Method | URL | Description |
|---|---|---|
| POST | `/api/ticket/book` | Book a ticket (ISSUE relationship) |
| GET | `/api/ticket/{id}` | Get ticket details |
| GET | `/api/tickets/passenger/{id}` | Get all tickets for a passenger |
| DELETE | `/api/ticket/{id}/cancel` | Cancel a ticket |

### Payment
| Method | URL | Description |
|---|---|---|
| GET | `/api/payment/{id}` | Get payment info |
| PUT | `/api/payment/{id}/complete` | Mark payment as Done |

### Supervisor (Admin)
| Method | URL | Description |
|---|---|---|
| POST | `/api/supervisor/login` | Supervisor login |
| GET | `/api/supervisor/trains` | View all trains |
| POST | `/api/supervisor/trains` | Add a new train (MANAGE) |
| PUT | `/api/supervisor/trains/{no}` | Update train |
| DELETE | `/api/supervisor/trains/{no}` | Delete train |
| GET | `/api/supervisor/all-tickets` | View all reservations |

---

## 🛠️ Tech Stack
- **Backend**: Python 3 + Flask (beginner-friendly!)
- **Database**: MySQL
- **Frontend**: Plain HTML + CSS + JavaScript (no frameworks needed)
