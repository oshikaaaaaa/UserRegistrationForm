from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Table, MetaData, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from fastapi.responses import HTMLResponse, RedirectResponse
import bcrypt  # Import bcrypt for password hashing


app = FastAPI()

# Database connection setup
DATABASE_URL = "mysql+pymysql://root:Cooperation322060#@localhost:3306/management_system"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Templates for rendering HTML
templates = Jinja2Templates(directory="templates")

# Static files (CSS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Routes
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


        
@app.post("/add", response_class=HTMLResponse)
def add_user(request: Request, name: str = Form(...), email: str = Form(...), password: str = Form(...), dob: str = Form(...)):
    try:
        db = SessionLocal()
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        
        # Use SQLAlchemy's text() to run raw SQL
        sql_query = text("""
            INSERT INTO users (name, email, password, dob) 
            VALUES (:name, :email, :password, :dob)
        """)

        # Execute the query
        db.execute(sql_query, {"name": name, "email": email, "password": hashed_password.decode("utf-8"), "dob": dob})
        db.commit()
        db.close()

        response = RedirectResponse(url="/dashboard", status_code=302)
        response.set_cookie("is_admin", "false")  # Set cookie to indicate the user is not an admin
        return response

    except SQLAlchemyError as e:
        db.rollback()
        return templates.TemplateResponse("index.html", {"request": request, "error": str(e)})

# Login Routes
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})




@app.post("/login", response_class=HTMLResponse)
def login(request: Request, email: str = Form(...), password: str = Form(...)):
    try:
        db = SessionLocal()

        # Fetch the user from the database
        sql_query = text("SELECT * FROM users WHERE email = :email")
        user = db.execute(sql_query, {"email": email}).fetchone()
        db.close()

        if user:
            # Extract the hashed password from the database
            hashed_password = user["password"]

            # Verify the password
            if bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8")):
                if email == "admin@gmail.com":  # Check for admin email
                    response = RedirectResponse(url="/admin", status_code=302)
                    response.set_cookie("is_admin", "true")  # Set cookie to indicate the user is an admin
                    return response
                else:
                    response = RedirectResponse(url="/dashboard", status_code=302)
                    response.set_cookie("is_admin", "false")  # Set cookie to indicate the user is not an admin
                    return response
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid email or password"})

    except SQLAlchemyError as e:
        return templates.TemplateResponse("login.html", {"request": request, "error": str(e)})



# Dashboard Route (A sample page after login)
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    # Check if the user is an admin
    is_admin = request.cookies.get("is_admin") == "true"
    
    if not is_admin:
        return RedirectResponse(url="/login")
    else:
        try:
            db = SessionLocal()

            # Query to fetch all users from the database
            sql_query = text("SELECT * FROM users")
            users = db.execute(sql_query).fetchall()

            db.close()

            # Render the admin page and pass the list of users
            return templates.TemplateResponse("admin.html", {"request": request, "users": users})

        except SQLAlchemyError as e:
            return templates.TemplateResponse("admin.html", {"request": request, "error": str(e)})


@app.get("/logout", response_class=HTMLResponse)
def logout(request: Request):
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("is_admin")  # Delete the cookie
    return response

