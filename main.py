import os
from fastapi import FastAPI, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
import re
from starlette.middleware.sessions import SessionMiddleware
from database import init_db, get_db, SessionLocal, User, Product, Transaction

app = FastAPI()
SESSION_SECRET = os.getenv("SESSION_SECRET", "change-me-in-production")
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()
    # Create default admin user if it doesn't exist
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.student_id == 0).first()
        if not admin:
            admin = User(
                name="Admin",
                student_id=0,  # Admin student_id: 0
                password=1234,  # Default admin password: 1234
                points=0,
                is_admin=True
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()

def validate_password(password: str) -> bool:
    """Validate password: must be exactly 4 digits"""
    if not password:
        return False
    if not password.isdigit():
        return False
    if len(password) != 4:
        return False
    return True

def validate_student_id(student_id: str) -> bool:
    """Validate StudentID: must be numeric and 9-10 digits"""
    if not student_id:
        return False
    if not student_id.isdigit():
        return False
    if len(student_id) < 9 or len(student_id) > 10:
        return False
    return True

def get_user_from_session(request: Request, db: Session):
    """Get current user from session"""
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Redirect to login if not authenticated, otherwise to dashboard"""
    user_id = request.session.get("user_id")
    if user_id:
        return RedirectResponse(url="/dashboard", status_code=303)
    return RedirectResponse(url="/login", status_code=303)

# Captive Portal Detection Endpoints
# These endpoints are used by devices to detect captive portals
# They redirect to home page to trigger captive portal login
@app.get("/generate_204")
async def generate_204(request: Request):
    """Android captive portal detection - redirects to home"""
    return RedirectResponse(url="/", status_code=302)

@app.get("/success.txt")
async def success_txt(request: Request):
    """iOS captive portal detection - redirects to home"""
    return RedirectResponse(url="/", status_code=302)

@app.get("/hotspot-detect.html")
async def hotspot_detect(request: Request):
    """iOS captive portal detection - redirects to home"""
    return RedirectResponse(url="/", status_code=302)

@app.get("/connecttest.txt")
async def connecttest_txt(request: Request):
    """Windows captive portal detection - redirects to home"""
    return RedirectResponse(url="/", status_code=302)

@app.get("/ncsi.txt")
async def ncsi_txt(request: Request):
    """Windows Network Connectivity Status Indicator - redirects to home"""
    return RedirectResponse(url="/", status_code=302)

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("login.html", {"request": request, "mode": "login"})

@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    """Signup page"""
    return templates.TemplateResponse("login.html", {"request": request, "mode": "signup"})

@app.post("/api/login")
async def login(
    request: Request,
    student_id: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Handle login"""
    if not validate_student_id(student_id):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "mode": "login", "error": "Invalid StudentID. Must be 9-10 digits."}
        )
    
    if not validate_password(password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "mode": "login", "error": "Invalid password. Must be exactly 4 digits."}
        )
    
    # Convert student_id to integer
    try:
        student_id_int = int(student_id)
    except ValueError:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "mode": "login", "error": "Invalid StudentID. Must be numeric."}
        )
    
    user = db.query(User).filter(User.student_id == student_id_int).first()
    if not user or user.password != int(password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "mode": "login", "error": "Invalid StudentID or password."}
        )
    
    request.session["user_id"] = user.id
    request.session["is_admin"] = user.is_admin
    
    if user.is_admin:
        return RedirectResponse(url="/admin", status_code=303)
    return RedirectResponse(url="/dashboard", status_code=303)

@app.post("/api/signup")
async def signup(
    request: Request,
    name: str = Form(...),
    student_id: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Handle signup"""
    if not validate_student_id(student_id):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "mode": "signup", "error": "Invalid StudentID. Must be 9-10 digits."}
        )
    
    if not validate_password(password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "mode": "signup", "error": "Invalid password. Must be exactly 4 digits."}
        )
    
    # Convert student_id to integer
    try:
        student_id_int = int(student_id)
    except ValueError:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "mode": "signup", "error": "Invalid StudentID. Must be numeric."}
        )
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.student_id == student_id_int).first()
    if existing_user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "mode": "signup", "error": "StudentID already exists."}
        )
    
    # Create new user
    new_user = User(
        name=name,
        student_id=student_id_int,
        password=int(password),
        points=0,
        is_admin=False
    )
    db.add(new_user)
    db.commit()
    
    request.session["user_id"] = new_user.id
    request.session["is_admin"] = False
    
    return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db), error: str = None):
    """User dashboard"""
    user = get_user_from_session(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    if user.is_admin:
        return RedirectResponse(url="/admin", status_code=303)
    
    # Get error from query params if not passed
    if not error:
        error = request.query_params.get("error")
    
    # Get products
    products = db.query(Product).all()
    
    # Get user transactions
    transactions = db.query(Transaction).filter(
        Transaction.user_id == user.id
    ).order_by(Transaction.timestamp.desc()).limit(10).all()
    
    # Calculate user rank
    all_users = db.query(User).filter(User.is_admin == False).order_by(User.points.desc()).all()
    user_rank = next((i + 1 for i, u in enumerate(all_users) if u.id == user.id), len(all_users) + 1)
    
    # Get top 6 users
    top_users = all_users[:6]
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "products": products,
        "transactions": transactions,
        "user_rank": user_rank,
        "top_users": top_users,
        "error": error
    })

@app.post("/api/purchase")
async def purchase(
    request: Request,
    product_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """Handle product purchase"""
    user = get_user_from_session(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return RedirectResponse(url="/dashboard?error=Product not found", status_code=303)
    
    if product.stock_quantity <= 0:
        return RedirectResponse(url="/dashboard?error=Product out of stock", status_code=303)
    
    if user.points < product.cost_points:
        return RedirectResponse(url="/dashboard?error=Insufficient points", status_code=303)
    
    # Process purchase
    user.points -= product.cost_points
    product.stock_quantity -= 1
    
    # Create transaction
    transaction = Transaction(
        user_id=user.id,
        item_name=product.name,
        point_change=-product.cost_points,
        timestamp=datetime.utcnow()
    )
    db.add(transaction)
    db.commit()
    
    return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request, db: Session = Depends(get_db)):
    """Admin panel"""
    user = get_user_from_session(request, db)
    if not user or not user.is_admin:
        return RedirectResponse(url="/login", status_code=303)
    
    # Get all users (excluding admin)
    users = db.query(User).filter(User.is_admin == False).all()
    total_users = len(users)
    
    # Get all products
    products = db.query(Product).all()
    
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "admin": user,
        "users": users,
        "total_users": total_users,
        "products": products
    })

@app.post("/api/admin/delete-user")
async def delete_user(
    request: Request,
    user_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """Delete a user"""
    admin = get_user_from_session(request, db)
    if not admin or not admin.is_admin:
        return RedirectResponse(url="/login", status_code=303)
    
    user = db.query(User).filter(User.id == user_id).first()
    if user and not user.is_admin:
        # Delete user's transactions
        db.query(Transaction).filter(Transaction.user_id == user_id).delete()
        db.delete(user)
        db.commit()
    
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/api/admin/update-points")
async def update_user_points(
    request: Request,
    user_id: int = Form(...),
    points: int = Form(...),
    db: Session = Depends(get_db)
):
    """Update user points"""
    admin = get_user_from_session(request, db)
    if not admin or not admin.is_admin:
        return RedirectResponse(url="/login", status_code=303)
    
    user = db.query(User).filter(User.id == user_id).first()
    if user and not user.is_admin:
        user.points = max(0, points)  # Ensure points are not negative
        db.commit()
    
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/api/admin/delete-all-users")
async def delete_all_users(
    request: Request,
    db: Session = Depends(get_db)
):
    """Delete all users (except admin)"""
    admin = get_user_from_session(request, db)
    if not admin or not admin.is_admin:
        return RedirectResponse(url="/login", status_code=303)
    
    # Delete all non-admin users and their transactions
    users = db.query(User).filter(User.is_admin == False).all()
    for user in users:
        db.query(Transaction).filter(Transaction.user_id == user.id).delete()
        db.delete(user)
    db.commit()
    
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/api/admin/update-stock")
async def update_product_stock(
    request: Request,
    product_id: int = Form(...),
    stock_quantity: int = Form(...),
    db: Session = Depends(get_db)
):
    """Update product stock quantity"""
    admin = get_user_from_session(request, db)
    if not admin or not admin.is_admin:
        return RedirectResponse(url="/login", status_code=303)
    
    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        product.stock_quantity = max(0, stock_quantity)  # Ensure stock is not negative
        db.commit()
    
    return RedirectResponse(url="/admin", status_code=303)

@app.get("/logout")
async def logout(request: Request):
    """Logout"""
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))

