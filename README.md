# ecovendíx - Recycle / Shop Machine

A web application for managing recycling points and shopping system built with FastAPI and MySQL.

## Features

- **User Authentication**: Login and signup with StudentID validation (9-10 digits)
- **User Dashboard**: 
  - Shop section with products
  - Transaction history
  - User ranking and leaderboard
- **Admin Panel**: User management with delete functionality

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure MySQL database:**
   - Create a MySQL database named `ecovendix` (or your preferred name)
   - Create a `.env` file in the project root with the following variables:
     ```
     MYSQL_USER=root
     MYSQL_PASSWORD=your_password
     MYSQL_HOST=localhost
     MYSQL_PORT=3306
     MYSQL_DATABASE=ecovendix
     ```
   - If no `.env` file is provided, the application will use default values (user: root, password: empty, host: localhost, port: 3306, database: ecovendix)

3. **Run the application:**
   ```bash
   python main.py
   ```
   
   Or using uvicorn directly:
   ```bash
   uvicorn main:app --reload
   ```

4. **Access the application:**
   - Open your browser and go to `http://localhost:8000`
   - Default admin credentials:
     - StudentID: `000000000`
     - Password: `admin123`

## Database

The application uses MySQL and will automatically create the necessary tables on first run. The database is pre-seeded with:
- Default products (Water, Drink, Soda, Snacks, Chocolate, Biscuit)
- An admin user

## Project Structure

```
.
├── main.py              # FastAPI application and routes
├── database.py          # Database models and setup
├── requirements.txt     # Python dependencies
├── templates/          # HTML templates
│   ├── login.html      # Login/Signup page
│   ├── dashboard.html  # User dashboard
│   └── admin.html      # Admin panel
├── static/             # Static files (CSS, images, icons)
│   └── style.css       # Main stylesheet
└── .env                # Environment variables for MySQL configuration (create this file)
```

## StudentID Validation

StudentID must be:
- Numeric only
- Between 9 and 10 digits in length

## Default Products

- Water: 15 points
- Drink: 25 points
- Soda: 35 points
- Snacks: 30 points
- Chocolate: 50 points
- Biscuit: 30 points

