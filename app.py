from flask import Flask, render_template, request, redirect, session, flash, url_for
from werkzeug.utils import secure_filename
import sqlite3
import os
from datetime import datetime, timedelta
from datetime import date




app = Flask(__name__)
app.secret_key = 'your_secret_key'

DB_PATH = 'lms.db'




'''
def generate_center_code():
    conn = sqlite3.connect('lms.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM centers")
    count = cursor.fetchone()[0] + 1
    conn.close()
    return f"C{str(count).zfill(3)}"
'''



def init_db():
    conn = sqlite3.connect('lms.db')
    cursor = conn.cursor()
    
    # Create table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id TEXT UNIQUE,
            password TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS centers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            center_code TEXT UNIQUE,
            center_name TEXT,
            name TEXT,
            email TEXT,
            mobile TEXT,
            address TEXT,
            pin_code TEXT,
            state TEXT,
            photo TEXT,
            status TEXT DEFAULT 'Active',
            registration_date TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            center_code TEXT,
            center_name TEXT,
            mobile TEXT,
            start_date TEXT,
            valid_for TEXT,
            end_date TEXT,
            status TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT,
            uploaded_by TEXT,         -- 'admin' or 'center'
            center_code TEXT,         -- nullable for admin
            course_title TEXT,
            course_duration TEXT,
            thumbnail TEXT,
            upload_date TEXT
        )
    ''')

    cursor.execute('''
       CREATE TABLE IF NOT EXISTS modules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER,
            module_title TEXT,
            FOREIGN KEY(course_id) REFERENCES courses(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_id INTEGER,
            lesson_title TEXT,
            video_link TEXT,
            pdf_path TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT UNIQUE,
            center_code TEXT,
            batch_id TEXT,
            name TEXT,
            father_name TEXT,
            dob TEXT,
            gender TEXT,
            mobile TEXT,
            alt_mobile TEXT,
            email TEXT,
            address TEXT,
            city TEXT,
            pin_code TEXT,
            state TEXT,
            qualification TEXT,
            passing_year TEXT,
            school TEXT,
            board TEXT,
            admission_date TEXT,
            photo TEXT,
            status TEXT DEFAULT 'Active'
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            center_code TEXT,
            adjustment_id INTEGER,
            batch_id TEXT,
            payment_date TEXT,
            actual_payment_date TEXT,
            payment_amount REAL,
            balance_amount REAL,
            payment_mode TEXT,
            payment_status TEXT,
            installment_name TEXT,
            remarks TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_code TEXT UNIQUE,
            batch_name TEXT,
            batch_time TEXT,
            duration TEXT,
            start_date TEXT,
            status TEXT,
            center_code TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS batch_students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id INTEGER,
            student_id INTEGER,
            FOREIGN KEY (batch_id) REFERENCES batches(id),
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            batch_id INTEGER,
            date TEXT,
            status TEXT CHECK(status IN ('Present', 'Absent')),
            UNIQUE(student_id, batch_id, date),
            FOREIGN KEY(student_id) REFERENCES students(id),
            FOREIGN KEY(batch_id) REFERENCES batches(id)
        )
        ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS allowed_courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER,
            batch_id TEXT,
            center_code TEXT,
            assigned_date TEXT
        )
        ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            course_id INTEGER,
            assigned_date TEXT
        )
        ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER,
            module_id INTEGER,
            question_text TEXT,
            option_1 TEXT,
            option_2 TEXT,
            option_3 TEXT,
            option_4 TEXT,
            correct_option TEXT,
            FOREIGN KEY(course_id) REFERENCES courses(id),
            FOREIGN KEY(module_id) REFERENCES modules(id)
        )
        ''')

    cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_series (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            type TEXT,  -- Mock Test, Unit Test, etc.
            status TEXT,  -- Active, Pause, Inactive
            created_by TEXT,  -- 'admin' or center_code
            created_at TEXT,
            duration INTEGER DEFAULT 30
        )
        ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS test_series_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_series_id INTEGER,
            question_id INTEGER,
            UNIQUE(test_series_id, question_id)  -- Prevent duplicate question entries
        )
        ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS batch_test_series (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id INTEGER,
            test_id INTEGER
        )
        ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS test_series_allotments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_series_id INTEGER,
            batch_id INTEGER,
            center_code TEXT,
            assigned_at TEXT
        )
        ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS test_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            test_series_id INTEGER,
            question_id INTEGER,
            selected_option TEXT,
            correct_option TEXT,
            is_correct INTEGER,
            submitted_at TEXT,
            result_released INTEGER DEFAULT 0
        )''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS adjustments (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          student_id TEXT,
          center_code TEXT,
          adjust_date TEXT,
          amount REAL,
          reference_by TEXT,
          adjust_for TEXT,
          remarks TEXT,
          adjustment_id INTEGER
        )
        ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS live_classes (
          id                INTEGER PRIMARY KEY AUTOINCREMENT,
          title             TEXT    NOT NULL,
          start_time        TEXT    NOT NULL,     -- ISO e.g. "2025-08-05T14:30"
          end_time          TEXT,                   -- optional ISO
          conducted_by      TEXT,
          thumbnail         TEXT,                   -- relative path under static/
          created_by_center TEXT    NOT NULL
        )
        ''')

        # map live_class → batch
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS live_class_batches (
          id             INTEGER PRIMARY KEY AUTOINCREMENT,
          live_class_id  INTEGER NOT NULL,
          batch_id       TEXT    NOT NULL,
          FOREIGN KEY(live_class_id) REFERENCES live_classes(id)
        )
        ''')








    
    # Insert default admin only if not exists
    cursor.execute("SELECT * FROM admin WHERE admin_id = 'admin'")
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO admin (admin_id, password) VALUES (?, ?)", ('admin', 'admin123'))
        conn.commit()
    
    conn.close()





@app.route('/')
def homepage():
    return render_template('homepage.html')


# Admin Login
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        admin_id = request.form['admin_id']
        password = request.form['password']
        
        conn = sqlite3.connect('lms.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admin WHERE admin_id = ? AND password = ?", (admin_id, password))
        admin = cursor.fetchone()
        conn.close()

        if admin:
            # Invalidate any previous sessions
            session.clear()
            session['admin_logged_in'] = True
            session['admin_id'] = admin_id
            session['last_activity'] = datetime.now().isoformat()
            return redirect('/admin_panel')
        else:
            flash('Invalid Admin ID or Password', 'error')
    
    return render_template('admin/login.html')



from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect('/admin_login')

        # Auto logout after 5 minutes of inactivity
        last_activity = session.get('last_activity')
        if last_activity:
            last_active_time = datetime.fromisoformat(last_activity)
            if datetime.now() - last_active_time > timedelta(minutes=5):
                session.clear()
                flash('Session expired due to inactivity.', 'warning')
                return redirect('/admin_login')
        
        # Update activity time
        session['last_activity'] = datetime.now().isoformat()
        return f(*args, **kwargs)
    return decorated_function



# Admin Panel
@app.route('/admin_panel')
@admin_required
def admin_panel():
    if not session.get('admin_logged_in'):
        return redirect('/admin_login')
    return render_template('admin/admin_panel.html')






from flask import render_template, session, redirect
import sqlite3

@app.route('/admin/home')
def admin_home():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM centers")
    total_centers = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM courses")
    total_courses = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM test_series")
    total_test_series = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM questions")
    total_questions = c.fetchone()[0]

    conn.close()

    return render_template('admin/admin_panel_home.html',
                           total_centers=total_centers,
                           total_courses=total_courses,
                           total_test_series=total_test_series,
                           total_questions=total_questions)




# Logout Admin
@app.route('/admin_logout')
def admin_logout():
    session.clear()
    return redirect('/admin_login')



# ------------------------ Add New Center ----------------------------

# Route
@app.route('/add_center', methods=['GET', 'POST'])
def add_center():
    if not session.get('admin_logged_in'):
        return redirect('/admin_login')

    UPLOAD_FOLDER = 'static/uploads/centers'

    if request.method == 'POST':
        code = request.form['center_code']
        name = request.form['center_name']
        owner_name=request.form['owner_name']
        email = request.form['email']
        mobile = request.form['mobile']
        address = request.form['address']
        pin = request.form['pin_code']
        state = request.form['state']
        status = request.form['status']
        registration_date = datetime.now().strftime("%Y-%m-%d")

        # Save photo to the correct folder
        photo = request.files['photo']
        if photo and photo.filename != '':
            photo_name = secure_filename(photo.filename)
            photo_path = os.path.join(UPLOAD_FOLDER, photo_name)
            photo.save(photo_path)
        else:
            photo_name = ''  # default or error handling

        # Insert into DB
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO centers (center_code, center_name,name, email, mobile, address, pin_code, state, photo, status, registration_date)
            VALUES (?, ?,?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (code, name,owner_name, email, mobile, address, pin, state, photo_name, status, registration_date))
        conn.commit()
        conn.close()

        flash('Center added successfully!', 'success')
        return redirect('/add_center')

    return render_template('admin/add_center.html')

# ------------------------ Admin View Centers ---------------------------------
@app.route('/view_centers', methods=['GET', 'POST'])
def view_centers():
    if not session.get('admin_logged_in'):
        return redirect('/admin_login')

    search_term = request.form.get('search', '').strip()
    filter_status = request.form.get('status', '')

    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
        SELECT c.*, s.end_date 
        FROM centers c
        LEFT JOIN (
            SELECT center_code, MAX(end_date) AS end_date 
            FROM subscriptions 
            GROUP BY center_code
        ) s ON c.center_code = s.center_code
        WHERE 1=1
    """

    params = []
    if search_term:
        query += " AND (c.center_name LIKE ? OR c.center_code LIKE ?)"
        params.extend([f"%{search_term}%", f"%{search_term}%"])
    if filter_status:
        query += " AND c.status = ?"
        params.append(filter_status)

    query += " ORDER BY c.id DESC"
    cursor.execute(query, params)
    centers = cursor.fetchall()
    centers = [dict(c) for c in centers]

    for c in centers:
        if c.get('end_date'):
            try:
                end = datetime.strptime(c['end_date'], '%Y-%m-%d')
                remaining = (end - datetime.today()).days
                c['remaining_days'] = max(0, remaining)
            except:
                c['remaining_days'] = 'N/A'
        else:
            c['remaining_days'] = 'N/A'

    conn.close()
    return render_template('admin/view_centers.html', centers=centers, search_term=search_term, filter_status=filter_status)



# -------------------------------- Admin Edit Centers ------------------------

@app.route('/edit_center/<int:center_id>', methods=['GET', 'POST'])
def edit_center(center_id):
    if not session.get('admin_logged_in'):
        return redirect('/admin_login')

    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    UPLOAD_FOLDER = 'static/uploads/centers'

    if request.method == 'POST':
        center_name = request.form['center_name']
        name=request.form['owner_name']
        email = request.form['email']
        mobile = request.form['mobile']
        address = request.form['address']
        pin_code = request.form['pin_code']
        state = request.form['state']
        status = request.form['status']

        # Check if a new photo is uploaded
        photo = request.files.get('photo')
        if photo and photo.filename != '':
            photo_name = secure_filename(photo.filename)
            photo_path = os.path.join(UPLOAD_FOLDER, photo_name)
            photo.save(photo_path)

            cursor.execute('''
                UPDATE centers SET 
                    center_name=?, name=?, email=?, mobile=?, address=?, pin_code=?, state=?, status=?, photo=?
                WHERE id=?
            ''', (center_name, name, email, mobile, address, pin_code, state, status, photo_name, center_id))
        else:
            cursor.execute('''
                UPDATE centers SET 
                    center_name=?, name=?, email=?, mobile=?, address=?, pin_code=?, state=?, status=?
                WHERE id=?
            ''', (center_name, name, email, mobile, address, pin_code, state, status, center_id))

        conn.commit()
        conn.close()
        flash("Center updated successfully!", "success")
        return redirect('/view_centers')

    cursor.execute("SELECT * FROM centers WHERE id=?", (center_id,))
    center = cursor.fetchone()
    conn.close()
    return render_template('admin/edit_center.html', center=center)

# ------------------- Admin Delete Centers -------------------------

@app.route('/delete_center/<int:center_id>')
def delete_center(center_id):
    if not session.get('admin_logged_in'):
        return redirect('/admin_login')

    conn = sqlite3.connect('lms.db')
    cursor = conn.cursor()

    # Get center_code before deletion
    cursor.execute("SELECT center_code, photo FROM centers WHERE id=?", (center_id,))
    row = cursor.fetchone()
    if not row:
        flash("Center not found!", "error")
        return redirect('/view_centers')

    center_code, photo = row

    # Delete subscriptions first
    cursor.execute("DELETE FROM subscriptions WHERE center_code=?", (center_code,))
    # Delete center
    cursor.execute("DELETE FROM centers WHERE id=?", (center_id,))
    conn.commit()
    conn.close()

    # Remove photo from filesystem (optional)
    try:
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], photo))
    except:
        pass

    flash("Center and related data deleted successfully!", "success")
    return redirect('/view_centers')



# ---------------------- Admin Manage Subscription -------------------------
@app.route('/manage_subscription/<center_code>', methods=['GET', 'POST'])
def manage_subscription(center_code):
    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get center details
    cursor.execute("SELECT * FROM centers WHERE center_code = ?", (center_code,))
    center = cursor.fetchone()

    if not center:
        flash('Center not found!', 'error')
        return redirect('/view_centers')

    # Get the latest subscription (if any)
    cursor.execute("SELECT * FROM subscriptions WHERE center_code = ? ORDER BY start_date DESC LIMIT 1", (center_code,))
    subscription = cursor.fetchone()

    if request.method == 'POST':
        start_date = request.form['start_date']
        valid_for = request.form['valid_for']
        end_date = request.form['end_date']
        status = request.form['status']

        if subscription:
            # Update the existing subscription
            cursor.execute("""
                UPDATE subscriptions
                SET start_date = ?, valid_for = ?, end_date = ?, status = ?
                WHERE id = ?
            """, (start_date, valid_for, end_date, status, subscription['id']))
            flash('Subscription updated successfully!', 'success')
        else:
            # Insert new subscription if not exists
            cursor.execute("""
                INSERT INTO subscriptions (center_code, center_name, mobile, start_date, valid_for, end_date, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                center['center_code'],
                center['center_name'],
                center['mobile'],
                start_date,
                valid_for,
                end_date,
                status
            ))
            flash('Subscription added successfully!', 'success')

        conn.commit()
        conn.close()
        return redirect('/view_centers')

    return render_template('admin/manage_subscription.html',
                           center_code=center['center_code'],
                           center_name=center['center_name'],
                           mobile=center['mobile'],
                           subscription=subscription)


# ----------------------------- Admin or Center Add new Course -------------------
from flask import Flask, render_template, request, redirect, session
from werkzeug.utils import secure_filename
from datetime import datetime
import sqlite3
import os

@app.route('/add_course', methods=['GET', 'POST'])
def add_course():
    is_admin = session.get('admin_logged_in')
    is_center = session.get('center_logged_in')

    if not is_admin and not is_center:
        return redirect('/')

    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if request.method == 'POST':
        course_code = request.form.get('course_code', '').strip()
        course_title = request.form['course_title'].strip()
        course_duration = request.form['course_duration'].strip()
        upload_date = datetime.today().strftime('%Y-%m-%d')

        thumbnail = request.files.get('thumbnail')
        thumb_filename = None

        # If a new thumbnail is uploaded
        if thumbnail and thumbnail.filename != '':
            thumb_filename = secure_filename(thumbnail.filename)
            thumb_path = os.path.join('static/uploads/courses', thumb_filename)
            thumbnail.save(thumb_path)

        if course_code:  # UPDATE course
            if thumb_filename:
                cursor.execute('''
                    UPDATE courses
                    SET course_title = ?, course_duration = ?, thumbnail = ?
                    WHERE course_code = ?
                ''', (course_title, course_duration, thumb_filename, course_code))
            else:
                cursor.execute('''
                    UPDATE courses
                    SET course_title = ?, course_duration = ?
                    WHERE course_code = ?
                ''', (course_title, course_duration, course_code))
        else:  # INSERT new course
            if is_admin:
                uploaded_by = 'admin'
                center_code = None
                cursor.execute("SELECT COUNT(*) FROM courses WHERE uploaded_by='admin'")
                count = cursor.fetchone()[0] + 1
                course_code = f"ADM{str(count).zfill(3)}"
            else:
                uploaded_by = 'center'
                center_code = session.get('center_code')
                cursor.execute("SELECT COUNT(*) FROM courses WHERE uploaded_by='center' AND center_code=?", (center_code,))
                count = cursor.fetchone()[0] + 1
                course_code = f"{center_code}_C{count}"

            if not thumb_filename:
                conn.close()
                return "❌ Thumbnail is required for new course!", 400

            cursor.execute('''
                INSERT INTO courses (course_code, uploaded_by, center_code, course_title, course_duration, thumbnail, upload_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (course_code, uploaded_by, center_code, course_title, course_duration, thumb_filename, upload_date))

        conn.commit()
        conn.close()

        # Redirect based on user type
        if is_admin:
            return redirect('/view_courses')
        else:
            return redirect('/center/view_courses')

    # If GET → show form + course list
    if is_admin:
        cursor.execute("SELECT * FROM courses ORDER BY upload_date DESC")
    else:
        center_code = session.get('center_code')
        cursor.execute("SELECT * FROM courses WHERE center_code = ? ORDER BY upload_date DESC", (center_code,))

    courses = cursor.fetchall()
    conn.close()

    return render_template('add_course.html', courses=courses)





# ---------------------------- View Courses -----------------------------

@app.route('/view_courses', methods=['GET', 'POST'])
def view_courses():
    if not session.get('admin_logged_in') and not session.get('center_logged_in'):
        return redirect('/')

    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    search_term = request.form.get('search_term', '').strip()

    if session.get('admin_logged_in'):
        if search_term:
            cursor.execute("""
                SELECT * FROM courses
                WHERE course_title LIKE ? OR course_code LIKE ? OR center_code LIKE ?
                ORDER BY upload_date DESC
            """, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
        else:
            cursor.execute("SELECT * FROM courses ORDER BY upload_date DESC")
    else:
        center_code = session.get('center_code')
        if search_term:
            cursor.execute("""
                SELECT * FROM courses
                WHERE center_code = ? AND (
                    course_title LIKE ? OR course_code LIKE ?
                )
                ORDER BY upload_date DESC
            """, (center_code, f"%{search_term}%", f"%{search_term}%"))
        else:
            cursor.execute("SELECT * FROM courses WHERE center_code = ? ORDER BY upload_date DESC", (center_code,))

    courses = cursor.fetchall()
    conn.close()

    return render_template('admin/view_courses.html', courses=courses, search_term=search_term)




# --------------------------- Center View Courses -------------------------------


@app.route('/center/view_courses', methods=['GET', 'POST'])
def center_view_courses():
    if not session.get('center_logged_in'):
        return redirect('/center_login')

    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    center_code = session.get('center_code')
    search_term = request.form.get('search_term', '').strip()

    if search_term:
        cursor.execute("""
            SELECT * FROM courses
            WHERE center_code = ? AND (
                course_title LIKE ? OR course_code LIKE ?
            )
            ORDER BY upload_date DESC
        """, (center_code, f"%{search_term}%", f"%{search_term}%"))
    else:
        cursor.execute("""
            SELECT * FROM courses
            WHERE center_code = ?
            ORDER BY upload_date DESC
        """, (center_code,))

    courses = cursor.fetchall()
    conn.close()

    return render_template('center/view_courses.html', courses=courses, search_term=search_term)


# ----------------------------- Center Watch Course ------------------------------

@app.route('/center/watch_courses', methods=['GET', 'POST'])
def watch_courses():
    if not session.get('center_logged_in'):
        return redirect('/center_login')

    center_code = session.get('center_code')
    filter_by = request.form.get('filter_by', 'all')  # default is all

    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if filter_by == 'admin':
        cursor.execute("SELECT * FROM courses WHERE uploaded_by = 'admin'")
    elif filter_by == 'center':
        cursor.execute("SELECT * FROM courses WHERE uploaded_by = 'center' AND center_code = ?", (center_code,))
    else:  # all
        cursor.execute("""
            SELECT * FROM courses
            WHERE uploaded_by = 'admin' OR (uploaded_by = 'center' AND center_code = ?)
        """, (center_code,))

    courses = cursor.fetchall()
    conn.close()

    return render_template('center/watch_courses.html', courses=courses, selected_filter=filter_by)





@app.route('/center/view_course/<int:course_id>')
def view_course_modules_center(course_id):
    if not session.get('center_logged_in'):
        return redirect('/center_login')

    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Fetch course info
    cursor.execute("SELECT * FROM courses WHERE id=?", (course_id,))
    course = cursor.fetchone()

    # Fetch modules of the course
    cursor.execute("SELECT * FROM modules WHERE course_id=? ORDER BY id", (course_id,))
    modules = cursor.fetchall()

    conn.close()
    return render_template('center/view_course_modules.html', course=course, modules=modules)



@app.route('/center/view_module_lessons/<int:module_id>')
def view_module_lessons(module_id):
    if not session.get('center_logged_in'):
        return redirect('/center_login')

    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get module and lessons
    cursor.execute("SELECT * FROM modules WHERE id=?", (module_id,))
    module = cursor.fetchone()

    cursor.execute("SELECT * FROM lessons WHERE module_id=?", (module_id,))
    lessons = cursor.fetchall()

    conn.close()
    return render_template('center/view_module_lessons.html', module=module, lessons=lessons)

# ------------------------------------ Live Class ----------------------------------

@app.route('/center/live_schedule', methods=['GET','POST'])
def live_schedule():
    if 'center_code' not in session:
        return redirect('/center_login')


    # ensure upload folder exists
    STD_FOLDER = os.path.join(app.root_path, 'static/uploads/students')
    os.makedirs(STD_FOLDER, exist_ok=True)
        
    center = session['center_code']
    conn = sqlite3.connect('lms.db')
    cur  = conn.cursor()

    if request.method == 'POST':
        # grab form
        title        = request.form['title']
        start_time   = request.form['start_time']    # e.g. "2025-08-05T14:30"
        end_time     = request.form.get('end_time')
        conducted_by = request.form['conducted_by']

        # thumbnail
        thumb = request.files.get('thumbnail')
        thumb_path = ''
        if thumb and thumb.filename:
            fn = secure_filename(thumb.filename)
            thumb.save(os.path.join(STD_FOLDER, fn))
            thumb_path = os.path.join('uploads/live_thumbs', fn)

        # insert
        cur.execute('''
          INSERT INTO live_classes
            (title, start_time, end_time, conducted_by, thumbnail, created_by_center)
          VALUES (?,?,?,?,?,?)
        ''', (title, start_time, end_time, conducted_by, thumb_path, center))
        conn.commit()
        flash("✅ Live class scheduled.", "success")
        return redirect(url_for('live_schedule'))

    # GET: fetch classes + available batches
    cur.execute('SELECT * FROM live_classes WHERE created_by_center=? ORDER BY start_time', (center,))
    classes = [dict(id=r[0], title=r[1], start_time=r[2], end_time=r[3],
                    conducted_by=r[4], thumbnail=r[5]) for r in cur.fetchall()]

    cur.execute("SELECT DISTINCT batch_id FROM students WHERE center_code=?", (center,))
    batches = [r[0] for r in cur.fetchall()]

    conn.close()
    return render_template('center/live_schedule.html',
                           classes=classes, batches=batches)

from datetime import datetime
import sqlite3
from flask import session, redirect, request, render_template, flash, url_for

@app.route('/center/assign_live_to_batch', methods=['GET', 'POST'])
def assign_live_to_batch():
    if 'center_code' not in session:
        return redirect('/center_login')

    center_code = session['center_code']
    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1️⃣ Fetch all live classes CREATED by this center
    cur.execute('''
      SELECT id, title 
      FROM live_classes 
      WHERE created_by_center = ?
      ORDER BY start_time DESC
    ''', (center_code,))
    classes = cur.fetchall()

    # 2️⃣ Fetch all batches of this center
    cur.execute('''
      SELECT id, batch_code, batch_name 
      FROM batches 
      WHERE center_code = ?
      ORDER BY batch_code
    ''', (center_code,))
    batches = cur.fetchall()

    message = ""

    if request.method == 'POST':
        # — Assign —
        if 'live_class_id' in request.form and 'batch_id' in request.form:
            live_class_id = int(request.form['live_class_id'])
            batch_id      = int(request.form['batch_id'])

            # check existing
            cur.execute('''
              SELECT 1 
              FROM live_class_batches 
              WHERE live_class_id = ? AND batch_id = ?
            ''', (live_class_id, batch_id))
            if not cur.fetchone():
                cur.execute('''
                  INSERT INTO live_class_batches (live_class_id, batch_id)
                  VALUES (?, ?)
                ''', (live_class_id, batch_id))
                conn.commit()
                flash("✅ Live class assigned to batch.", "success")
            else:
                flash("⚠️ This class is already assigned to that batch.", "warning")

        # — Remove assignment —
        elif 'remove_id' in request.form:
            lcb_id = int(request.form['remove_id'])
            cur.execute('DELETE FROM live_class_batches WHERE id = ?', (lcb_id,))
            conn.commit()
            flash("❌ Assignment removed.", "info")

    # 3️⃣ Fetch all current assignments for display
    cur.execute('''
      SELECT lcb.id          AS assign_id,
             lc.title        AS class_title,
             lc.start_time   AS when_,
             b.batch_code,
             b.batch_name
      FROM live_class_batches lcb
      JOIN live_classes    lc ON lcb.live_class_id = lc.id
      JOIN batches         b  ON lcb.batch_id     = b.id
      WHERE lc.created_by_center = ?
      ORDER BY b.batch_code, lc.start_time
    ''', (center_code,))
    assignments = cur.fetchall()

    conn.close()
    return render_template(
      'center/assign_live_to_batch.html',
      classes=classes,
      batches=batches,
      assignments=assignments
    )





from datetime import datetime, date

@app.route('/student/live_classes')
def student_live_classes():
    # 1) Ensure the student is logged in
    if 'student_logged_in' not in session:
        return redirect('/student_login')

    # 2) Lookup this student’s batch_id from the DB
    student_text_id = session.get('student_id')
    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    cur.execute("SELECT batch_id FROM students WHERE student_id = ?", (student_text_id,))
    row = cur.fetchone()
    if not row or not row['batch_id']:
        conn.close()
        flash("⚠️ आपको अभी कोई बैच असाइन नहीं किया गया है।", "warning")
        return redirect(url_for('student_profile'))

    batch = row['batch_id']

    # 3) Figure out which date to show (from query string or today)
    selected_date = request.args.get('date', date.today().isoformat())

    # 4) Fetch only classes for that batch AND that date
    #    (assuming start_time is stored like "YYYY-MM-DDThh:mm")
    cur.execute('''
      SELECT lc.id, lc.title, lc.start_time, lc.end_time,
             lc.conducted_by, lc.thumbnail
      FROM live_classes lc
      JOIN live_class_batches lcb 
        ON lc.id = lcb.live_class_id
      WHERE lcb.batch_id = ?
        AND substr(lc.start_time,1,10) = ?
      ORDER BY lc.start_time
    ''', (batch, selected_date))
    classes = [dict(r) for r in cur.fetchall()]
    conn.close()

    # 5) Render, passing in `selected_date` and a `now_iso` timestamp
    return render_template(
        'student/live_classes.html',
        classes=classes,
        selected_date=selected_date,
        now_iso=datetime.utcnow().isoformat()
    )


# ------------------------------------ Questions Section ----------------------------

@app.route('/add_question', methods=['GET', 'POST'])
def add_question():
    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # --- Detect User Type ---
    is_admin = 'admin_logged_in' in session
    is_center = 'center_code' in session
    center_code = session.get('center_code')

    # --- Handle POST request for Add/Update ---
    if request.method == 'POST':
        edit_id = request.form.get('edit_id')
        course_id = request.form['course_id']
        module_id = request.form['module_id']
        question_text = request.form['question']
        option_1 = request.form['option_1']
        option_2 = request.form['option_2']
        option_3 = request.form['option_3']
        option_4 = request.form['option_4']
        correct_option = request.form['correct_option']

        if edit_id:  # Update question
            cursor.execute('''
                UPDATE questions
                SET course_id=?, module_id=?, question_text=?, 
                    option_1=?, option_2=?, option_3=?, option_4=?, correct_option=?
                WHERE id=?
            ''', (course_id, module_id, question_text, option_1, option_2, option_3, option_4, correct_option, edit_id))
            flash("Question updated successfully!", "success")
        else:  # Insert new question
            cursor.execute('''
                INSERT INTO questions (
                    course_id, module_id, question_text, 
                    option_1, option_2, option_3, option_4, correct_option
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (course_id, module_id, question_text, option_1, option_2, option_3, option_4, correct_option))
            flash("Question added successfully!", "success")

        conn.commit()
        return redirect(url_for('add_question'))

    # --- For GET: Load form data ---
    if is_admin:
        cursor.execute("SELECT * FROM courses")
    elif is_center:
        cursor.execute("SELECT * FROM courses WHERE center_code = ?", (center_code,))
    else:
        return redirect('/admin_login')

    courses = cursor.fetchall()

    # --- Filters ---
    selected_course = request.args.get('course_id', type=int)
    selected_module = request.args.get('module_id', type=int)
    search_text = request.args.get('search', '')

    modules = []
    if selected_course:
        cursor.execute("SELECT * FROM modules WHERE course_id = ?", (selected_course,))
        modules = cursor.fetchall()

    # --- Pagination ---
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    conditions = []
    params = []

    if selected_course:
        conditions.append("q.course_id = ?")
        params.append(selected_course)
    if selected_module:
        conditions.append("q.module_id = ?")
        params.append(selected_module)
    if search_text:
        conditions.append("q.question_text LIKE ?")
        params.append(f"%{search_text}%")

    where_clause = 'WHERE ' + ' AND '.join(conditions) if conditions else ''

    # --- Count and fetch questions ---
    cursor.execute(f"SELECT COUNT(*) FROM questions q {where_clause}", params)
    total_questions = cursor.fetchone()[0]
    total_pages = (total_questions + per_page - 1) // per_page

    cursor.execute(f'''
        SELECT q.*, c.course_title, m.module_title
        FROM questions q
        JOIN courses c ON q.course_id = c.id
        JOIN modules m ON q.module_id = m.id
        {where_clause}
        ORDER BY q.id DESC
        LIMIT ? OFFSET ?
    ''', (*params, per_page, offset))

    questions = cursor.fetchall()
    conn.close()

    return render_template(
        'exam/add_question.html',
        courses=courses,
        modules=modules,
        questions=questions,
        selected_course=selected_course,
        selected_module=selected_module,
        search_text=search_text,
        page=page,
        total_pages=total_pages,
        is_admin=is_admin  # ✅ for showing/hiding bulk upload
    )


@app.route('/get_modules/<int:course_id>')
def get_modules(course_id):
    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM modules WHERE course_id = ?", (course_id,))
    modules = [dict(id=row['id'], title=row['module_title']) for row in cursor.fetchall()]
    return jsonify(modules)



@app.route('/delete_question/<int:id>')
def delete_question(id):
    conn = sqlite3.connect('lms.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM questions WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash("Question deleted successfully", "success")
    return redirect(url_for('view_questions'))

# Edit route would load an existing form similar to your add_question logic.





import pandas as pd
import sqlite3
from flask import request, flash, redirect, url_for
@app.route('/upload_questions', methods=['POST']) 
def upload_questions():
    if 'excel_file' not in request.files:
        flash("No file part", "danger")
        return redirect(url_for('add_question'))

    file = request.files['excel_file']
    if file.filename == '':
        flash("No selected file", "danger")
        return redirect(url_for('add_question'))

    try:
        df = pd.read_excel(file)

        if df.empty or 'Course Code' not in df.columns or 'Module Title' not in df.columns:
            flash("Invalid Excel format. Required columns: Course Code, Module Title", "danger")
            return redirect(url_for('add_question'))

        conn = sqlite3.connect('lms.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        for _, row in df.iterrows():
            course_code = row['Course Code']
            module_title = row['Module Title']

            # Get course_id from course_code
            cursor.execute("SELECT id FROM courses WHERE course_code = ?", (course_code,))
            course_row = cursor.fetchone()
            if not course_row:
                flash(f"Course Code '{course_code}' not found.", "danger")
                continue
            course_id = course_row['id']

            # Get module_id from module_title and course_id
            cursor.execute("SELECT id FROM modules WHERE module_title = ? AND course_id = ?", (module_title, course_id))
            module_row = cursor.fetchone()
            if not module_row:
                flash(f"Module '{module_title}' not found for course '{course_code}'.", "danger")
                continue
            module_id = module_row['id']

            # Insert question
            cursor.execute('''
                INSERT INTO questions (
                    course_id, module_id, question_text,
                    option_1, option_2, option_3, option_4, correct_option
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                course_id, module_id, row['Question'],
                row['Option 1'], row['Option 2'], row['Option 3'], row['Option 4'],
                row['Correct Option']
            ))

        conn.commit()
        conn.close()

        flash("Questions uploaded successfully!", "success")
        return redirect(url_for('add_question'))

    except Exception as e:
        flash(f"Error uploading questions: {str(e)}", "danger")
        return redirect(url_for('add_question'))



@app.route('/update_question/<int:question_id>', methods=['POST'])
def update_question(question_id):
    if 'admin_logged_in' not in session and 'center_code' not in session:
        return redirect('/admin_login')  # or redirect to center login based on your logic

    course_id = request.form['course_id']
    module_id = request.form['module_id']
    question_text = request.form['question_text']
    option_1 = request.form['option_1']
    option_2 = request.form['option_2']
    option_3 = request.form['option_3']
    option_4 = request.form['option_4']
    correct_option = request.form['correct_option']

    conn = sqlite3.connect('lms.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE questions
        SET course_id=?, module_id=?, question_text=?, 
            option_1=?, option_2=?, option_3=?, option_4=?, correct_option=?
        WHERE id=?
    ''', (course_id, module_id, question_text, option_1, option_2, option_3, option_4, correct_option, question_id))
    conn.commit()
    conn.close()

    flash("Question updated successfully!", "success")
    return redirect(url_for('view_questions'))


@app.route('/edit_question/<int:question_id>')
def edit_question(question_id):
    # Determine user type based on session
    if 'admin_logged_in' in session:
        user_type = 'admin'
    elif 'center_code' in session:
        user_type = 'center'
    else:
        flash("Please log in first.", "warning")
        return redirect('/admin_login')  # Or use center login if needed

    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Fetch the question
    cursor.execute("SELECT * FROM questions WHERE id = ?", (question_id,))
    question = cursor.fetchone()

    if not question:
        flash("Question not found.", "danger")
        return redirect('/manage_questions')

    # Get courses
    if user_type == 'admin':
        cursor.execute("SELECT * FROM courses")
    else:
        cursor.execute("SELECT * FROM courses WHERE center_code = ?", (session['center_code'],))
    courses = cursor.fetchall()

    # Get modules for the selected course
    cursor.execute("SELECT * FROM modules WHERE course_id = ?", (question['course_id'],))
    modules = cursor.fetchall()

    conn.close()

    return render_template(
        'exam/edit_question.html',
        question=question,
        courses=courses,
        modules=modules,
        user_type=user_type
    )





@app.route('/download_question_template')
def download_question_template():
    output = io.BytesIO()
    df = pd.DataFrame(columns=[
        'Course Code', 'Module Title', 'Question',
        'Option 1', 'Option 2', 'Option 3', 'Option 4', 'Correct Option'
    ])
    df.to_excel(output, index=False)
    output.seek(0)

    return send_file(
        output,
        download_name='question_upload_template.xlsx',
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )



@app.route('/view_questions', methods=['GET', 'POST'])
def view_questions():
    if 'admin_logged_in' not in session and 'center_code' not in session:
        return redirect('/')

    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    is_admin = 'admin_logged_in' in session
    center_code = session.get('center_code')

    # Get list of courses
    if is_admin:
        cursor.execute("SELECT * FROM courses")
    else:
        cursor.execute("SELECT * FROM courses WHERE center_code = ?", (center_code,))
    courses = cursor.fetchall()

    selected_course = request.args.get('course_id')
    selected_module = request.args.get('module_id')
    search_text = request.args.get('search', '')

    # Get modules for selected course
    modules = []
    if selected_course:
        cursor.execute("SELECT * FROM modules WHERE course_id = ?", (selected_course,))
        modules = cursor.fetchall()

    # Build query
    query = '''
        SELECT q.*, c.course_title, m.module_title
        FROM questions q
        JOIN courses c ON q.course_id = c.id
        JOIN modules m ON q.module_id = m.id
    '''
    conditions = []
    params = []

    if not is_admin:
        conditions.append("c.center_code = ?")
        params.append(center_code)

    if selected_course:
        conditions.append("q.course_id = ?")
        params.append(selected_course)

    if selected_module:
        conditions.append("q.module_id = ?")
        params.append(selected_module)

    if search_text:
        conditions.append("q.question_text LIKE ?")
        params.append(f"%{search_text}%")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY q.id DESC"
    cursor.execute(query, params)
    questions = cursor.fetchall()

    conn.close()

    return render_template("exam/view_questions.html",
                           courses=courses,
                           modules=modules,
                           questions=questions,
                           selected_course=selected_course,
                           selected_module=selected_module,
                           search_text=search_text,
                           is_admin=is_admin)


# ------------------------------Test Series--------------------------------------
@app.route('/manage_test_series', methods=['GET', 'POST'])
def manage_test_series():
    if 'admin_logged_in' not in session and 'center_code' not in session:
        return redirect('/')

    created_by = 'admin' if 'admin_logged_in' in session else session['center_code']
    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Add or Update
    if request.method == 'POST':
        test_id = request.form.get('test_id')
        name = request.form['name']
        type_ = request.form['type']
        status = request.form['status']
        duration = request.form['duration'] or 30  # Default to 30 if not filled
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if test_id:  # Update
            cursor.execute("UPDATE test_series SET name = ?, type = ?, status = ?, duration = ? WHERE id = ?",
                           (name, type_, status, duration, test_id))
        else:  # Add
            cursor.execute("INSERT INTO test_series (name, type, status, duration, created_by, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                           (name, type_, status, duration, created_by, created_at))

        conn.commit()

    # Fetch all test series
    if 'admin_logged_in' in session:
        cursor.execute("SELECT * FROM test_series ORDER BY created_at DESC")
    else:
        cursor.execute("SELECT * FROM test_series WHERE created_by = ? ORDER BY created_at DESC", (created_by,))

    tests = cursor.fetchall()
    conn.close()
    return render_template('exam/manage_test_series.html', tests=tests)


@app.route('/delete_series/<int:test_id>')
def delete_series(test_id):
    conn = sqlite3.connect('lms.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM test_series WHERE id = ?", (test_id,))
    cursor.execute("DELETE FROM test_series_questions WHERE test_series_id = ?", (test_id,))
    cursor.execute("DELETE FROM test_batch_allow WHERE test_series_id = ?", (test_id,))
    conn.commit()
    conn.close()
    flash("Test Series Deleted", "success")
    return redirect('/manage_test_series')




@app.route('/view_test_series')
def view_test_series():
    if 'admin_logged_in' not in session and 'center_code' not in session:
        return redirect('/')

    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if 'admin_logged_in' in session:
        cursor.execute('SELECT * FROM test_series ORDER BY created_at DESC')
    else:
        center_code = session['center_code']
        cursor.execute('''
            SELECT * FROM test_series 
            WHERE created_by = ?
            ORDER BY created_at DESC
        ''', (center_code,))

    test_series = cursor.fetchall()

    # Get question count for each test
    test_question_counts = {}
    for test in test_series:
        cursor.execute('SELECT COUNT(*) as qcount FROM test_series_questions WHERE test_series_id = ?', (test['id'],))
        test_question_counts[test['id']] = cursor.fetchone()['qcount']

    conn.close()
    return render_template('exam/view_test_series.html',
                           test_series=test_series,
                           question_counts=test_question_counts)





@app.route('/add_questions_to_series/<int:series_id>', methods=['GET', 'POST'])
def add_questions_to_series(series_id):
    if 'admin_logged_in' not in session and 'center_code' not in session:
        return redirect('/')

    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    selected_module = request.args.get('module')
    module_filter = ""
    module_param = ()

    if selected_module:
        module_filter = " AND q.module_id = ?"
        module_param = (selected_module,)

    # Get modules (admin or center)
    if 'admin_logged_in' in session:
        cursor.execute("SELECT DISTINCT m.id, m.module_title FROM modules m")
    else:
        center_code = session['center_code']
        cursor.execute('''
            SELECT DISTINCT m.id, m.module_title
            FROM modules m
            JOIN courses c ON m.course_id = c.id
            WHERE c.center_code = ?
        ''', (center_code,))
    modules = cursor.fetchall()

    # Fetch questions not already in test
    if 'admin_logged_in' in session:
        cursor.execute(f'''
            SELECT q.*, c.course_title, m.module_title
            FROM questions q
            JOIN courses c ON q.course_id = c.id
            JOIN modules m ON q.module_id = m.id
            WHERE q.id NOT IN (
                SELECT question_id FROM test_series_questions WHERE test_series_id = ?
            ) {module_filter}
        ''', (series_id,) + module_param)
    else:
        cursor.execute(f'''
            SELECT q.*, c.course_title, m.module_title
            FROM questions q
            JOIN courses c ON q.course_id = c.id
            JOIN modules m ON q.module_id = m.id
            WHERE c.center_code = ?
            AND q.id NOT IN (
                SELECT question_id FROM test_series_questions WHERE test_series_id = ?
            ) {module_filter}
        ''', (session['center_code'], series_id) + module_param)
    questions = cursor.fetchall()

    # POST: Add selected questions
    if request.method == 'POST':
        selected_ids = request.form.getlist('question_ids')
        for qid in selected_ids:
            cursor.execute("INSERT OR IGNORE INTO test_series_questions (test_series_id, question_id) VALUES (?, ?)",
                           (series_id, qid))
        conn.commit()
        conn.close()
        flash(f"{len(selected_ids)} questions added!", "success")
        return redirect(f'/add_questions_to_series/{series_id}')

    conn.close()
    return render_template('exam/add_questions_to_series.html',
                           series_id=series_id,
                           modules=modules,
                           questions=questions,
                           selected_module=selected_module)






@app.route('/view_test_questions/<int:series_id>')
def view_test_questions(series_id):
    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT q.*
        FROM test_series_questions tsq
        JOIN questions q ON tsq.question_id = q.id
        WHERE tsq.test_series_id = ?
    ''', (series_id,))
    questions = cursor.fetchall()
    conn.close()

    # ⬇️  pass series_id to the template
    return render_template('exam/view_test_questions.html',
                           questions=questions,
                           series_id=series_id)




@app.route('/remove_question_from_series/<int:series_id>/<int:question_id>')
def remove_question_from_series(series_id, question_id):
    # Access control: must be admin or center
    if 'admin_logged_in' not in session and 'center_code' not in session:
        return redirect('/')

    conn = sqlite3.connect('lms.db')
    cursor = conn.cursor()

    # Delete the link (NOT the question itself)
    cursor.execute('''
        DELETE FROM test_series_questions
        WHERE test_series_id = ? AND question_id = ?
    ''', (series_id, question_id))
    conn.commit()
    conn.close()

    flash('Question removed from test‑series.', 'success')
    return redirect(f'/view_test_questions/{series_id}')


# ----------------------------- Assign Test to Batch ----------------------------
# app.py
from datetime import datetime
import sqlite3
from flask import session, redirect, request, render_template

@app.route('/assign_test_series_to_batch', methods=['GET', 'POST'])
def assign_test_series_to_batch():
    if 'center_code' not in session:
        return redirect('/center_login')

    center_code = session['center_code']
    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all batches of this center
    cursor.execute("SELECT * FROM batches WHERE center_code = ?", (center_code,))
    batches = cursor.fetchall()

    # Get test series (center or admin created)
    cursor.execute('''
        SELECT * FROM test_series 
        WHERE created_by = ? OR created_by = 'admin'
        ORDER BY created_at DESC
    ''', (center_code,))
    test_series = cursor.fetchall()

    message = ""

    if request.method == 'POST':
        if 'batch_id' in request.form and 'test_series_id' in request.form:
            batch_id = request.form['batch_id']
            test_series_id = request.form['test_series_id']
            assigned_at = datetime.now().strftime('%Y-%m-%d')

            cursor.execute('''
                SELECT * FROM test_series_allotments 
                WHERE batch_id = ? AND test_series_id = ?
            ''', (batch_id, test_series_id))
            exists = cursor.fetchone()

            if not exists:
                cursor.execute('''
                    INSERT INTO test_series_allotments (test_series_id, batch_id, center_code, assigned_at)
                    VALUES (?, ?, ?, ?)
                ''', (test_series_id, batch_id, center_code, assigned_at))
                conn.commit()
                message = "✅ Test Series assigned successfully."
            else:
                message = "⚠️ This Test Series is already assigned to this batch."

        elif 'remove' in request.form:
            batch_id = request.form['remove_batch_id']
            test_series_id = request.form['remove_test_series_id']
            cursor.execute('''
                DELETE FROM test_series_allotments 
                WHERE batch_id = ? AND test_series_id = ?
            ''', (batch_id, test_series_id))
            conn.commit()
            message = "❌ Assignment removed successfully."

    # Fetch all assignments
    cursor.execute('''
        SELECT tsa.id, b.batch_code, b.batch_name, ts.name AS test_name, ts.type, tsa.test_series_id, tsa.batch_id
        FROM test_series_allotments tsa
        JOIN batches b ON tsa.batch_id = b.id
        JOIN test_series ts ON tsa.test_series_id = ts.id
        WHERE tsa.center_code = ?
        ORDER BY b.batch_code
    ''', (center_code,))
    assignments = cursor.fetchall()

    conn.close()
    return render_template('center/assign_test_to_batch.html',
                           batches=batches,
                           test_series=test_series,
                           assignments=assignments,
                           message=message)


# ------------------------------ Student Test -----------------------------------

@app.route('/student/my_tests')
def student_my_tests():
    if 'student_id' not in session:
        return redirect('/student_login')

    student_id = session['student_id']  # This is the DB primary key (INTEGER)

    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 🔍 Fetch student full data
    cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
    student = cursor.fetchone()

    if not student:
        return "Student not found."

    batch_id = student['batch_id']
    center_code = student['center_code']

    # ✅ Use test_series_allotments instead of test_batch
    cursor.execute('''
        SELECT ts.*, (
            SELECT COUNT(*) FROM test_series_questions tsq 
            WHERE tsq.test_series_id = ts.id
        ) as total_questions
        FROM test_series ts
        JOIN test_series_allotments tsa ON ts.id = tsa.test_series_id
        WHERE tsa.batch_id = ?
        AND (ts.created_by = ? OR ts.created_by = 'admin')
    ''', (batch_id, center_code))

    tests = cursor.fetchall()

    return render_template('student/my_tests.html', tests=tests)


@app.route('/start_test/<int:test_id>')
def start_test(test_id):
    if 'student_logged_in' not in session:
        return redirect('/student_login')

    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get test series details (with duration)
    cursor.execute("SELECT * FROM test_series WHERE id = ?", (test_id,))
    test = cursor.fetchone()

    # Get all questions associated with the test series
    cursor.execute('''
        SELECT q.*
        FROM test_series_questions tsq
        JOIN questions q ON tsq.question_id = q.id
        WHERE tsq.test_series_id = ?
    ''', (test_id,))
    questions = cursor.fetchall()

    conn.close()

    return render_template('student/start_test.html', test=test, questions=questions, test_id=test_id, duration=test['duration'])




from datetime import datetime

@app.route('/finish_test/<int:test_id>', methods=['POST'])
def finish_test(test_id):
    if 'student_logged_in' not in session:
        return redirect('/student_login')

    student_id = session['student_id']
    submitted_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Check test type (Mock Test or not)
    cursor.execute('SELECT type FROM test_series WHERE id = ?', (test_id,))
    test_row = cursor.fetchone()
    if not test_row:
        conn.close()
        return "<h4>Invalid Test ID.</h4>"

    test_type = test_row['type']
    result_released = 1 if test_type.lower() == 'mock test' else 0

    # 🧹 Delete old results (overwrite logic)
    cursor.execute('DELETE FROM test_results WHERE student_id = ? AND test_series_id = ?', (student_id, test_id))

    # Get test questions
    cursor.execute('''
        SELECT q.id AS question_id, q.correct_option
        FROM test_series_questions tsq
        JOIN questions q ON tsq.question_id = q.id
        WHERE tsq.test_series_id = ?
    ''', (test_id,))
    questions = cursor.fetchall()

    # Mapping A/B/C/D → 1/2/3/4
    option_map = {'A': '1', 'B': '2', 'C': '3', 'D': '4'}

    for q in questions:
        question_id = q['question_id']
        correct_option = q['correct_option']
        selected_option = request.form.get(f'q{question_id}')  # A/B/C/D

        if selected_option and selected_option in option_map:
            selected_option_num = option_map[selected_option]  # '1'/'2'/...
            is_correct = int(selected_option_num == correct_option)
        else:
            selected_option = ''
            selected_option_num = ''
            is_correct = 0

        cursor.execute('''
            INSERT INTO test_results (
                student_id, test_series_id, question_id, selected_option,
                correct_option, is_correct, submitted_at, result_released
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            student_id, test_id, question_id, selected_option,
            correct_option, is_correct, submitted_at, result_released
        ))

    conn.commit()
    conn.close()
    return redirect(url_for('test_submit_success'))


@app.route('/test_submit_success')
def test_submit_success():
    return "<h2>✅ Test Submitted Successfully!</h2><p>Your responses have been saved.</p>"



# ----------------------------- Test Result Section ------------------------------------------

@app.route('/student/my_results')
def my_results():
    if 'student_logged_in' not in session:
        return redirect('/student_login')

    student_id = session['student_id']

    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # -----------------------------
    # Debug query to check raw data
    # -----------------------------
    print("Debug: Checking student test data for ID", student_id)
    cursor.execute('''
        SELECT ts.id, ts.name, ts.type, tr.result_released, tr.student_id, tr.submitted_at
        FROM test_results tr
        JOIN test_series ts ON tr.test_series_id = ts.id
        WHERE tr.student_id = ?
    ''', (student_id,))
    debug_data = cursor.fetchall()
    for row in debug_data:
        print(dict(row))

    # -----------------------------
    # Final query to show result
    # -----------------------------
    cursor.execute('''
        SELECT 
            ts.id AS test_series_id,
            ts.name AS test_name,
            MAX(tr.submitted_at) AS submitted_at,
            COUNT(tr.id) AS total_questions,
            SUM(CASE WHEN tr.is_correct = 1 THEN 1 ELSE 0 END) AS correct,
            SUM(CASE WHEN tr.is_correct = 0 THEN 1 ELSE 0 END) AS wrong
        FROM test_results tr
        JOIN test_series ts ON tr.test_series_id = ts.id
        WHERE tr.student_id = ? 
          AND (ts.type = 'Mock Test' OR tr.result_released = 1)
        GROUP BY ts.id
        ORDER BY submitted_at DESC
    ''', (student_id,))
    
    results = cursor.fetchall()
    conn.close()

    # Optional: Print what will be rendered
    print("Results to be displayed:")
    for r in results:
        print(dict(r))

    return render_template('student/my_results.html', results=results)



@app.route('/student/view_result_questions/<int:test_series_id>')
def view_result_questions(test_series_id):
    if 'student_id' not in session:
        return redirect('/student_login')

    student_id = session['student_id']
    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get student's answers with correct answer
    cursor.execute('''
        SELECT q.question_text, q.option_1, q.option_2, q.option_3, q.option_4,
               tr.selected_option, tr.correct_option, tr.is_correct
        FROM test_results tr
        JOIN questions q ON tr.question_id = q.id
        WHERE tr.student_id = ? AND tr.test_series_id = ?
    ''', (student_id, test_series_id))
    
    questions = cursor.fetchall()
    conn.close()

    return render_template('student/view_result_questions.html', questions=questions)


# ------------------------------- Center Result Section ----------------------------


from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from datetime import datetime

@app.route('/center/view_results')
def center_view_results():
    if 'center_code' not in session:
        return redirect('/center_login')

    center_code = session['center_code']

    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Use correct join based on student_id (not ID mismatch)
    cursor.execute('''
        SELECT 
            tr.student_id,
            s.name AS student_name,
            s.batch_id,
            tr.test_series_id,
            ts.name AS test_name,
            ts.type,
            MAX(tr.submitted_at) AS submitted_at,
            MAX(tr.result_released) AS result_released,
            COUNT(tr.question_id) AS total_questions,
            SUM(CASE WHEN tr.is_correct = 1 THEN 1 ELSE 0 END) AS correct_answers
        FROM test_results tr
        JOIN students s ON tr.student_id = s.id  -- ⚠️ here: use s.id not s.student_id
        JOIN test_series ts ON tr.test_series_id = ts.id
        WHERE s.center_code = ?
        GROUP BY tr.student_id, tr.test_series_id
        ORDER BY submitted_at DESC
    ''', (center_code,))
    
    results = cursor.fetchall()
    conn.close()

    return render_template('center/view_results.html', results=results)




@app.route('/center/toggle_result/<string:student_id>/<int:test_series_id>', methods=['POST'])
def toggle_result(student_id, test_series_id):
    if 'center_code' not in session:
        return redirect('/center_login')

    conn = sqlite3.connect('lms.db')
    cursor = conn.cursor()

    # पहले result_released की स्थिति प्राप्त करें
    cursor.execute('''
        SELECT result_released FROM test_results
        WHERE student_id = ? AND test_series_id = ?
    ''', (student_id, test_series_id))
    current_status = cursor.fetchone()

    if current_status:
        # Toggle the status: 0 → 1 or 1 → 0
        new_status = 0 if current_status[0] == 1 else 1

        cursor.execute('''
            UPDATE test_results
            SET result_released = ?
            WHERE student_id = ? AND test_series_id = ?
        ''', (new_status, student_id, test_series_id))

        conn.commit()

    conn.close()
    return redirect('/center/view_results')


@app.route('/center/review_result/<string:student_id>/<int:test_series_id>')
def review_result(student_id, test_series_id):
    if 'center_code' not in session:
        return redirect('/center_login')

    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get student's answers with correct option
    cursor.execute('''
        SELECT q.question_text, q.option_1, q.option_2, q.option_3, q.option_4,
               tr.selected_option, tr.correct_option, tr.is_correct
        FROM test_results tr
        JOIN questions q ON tr.question_id = q.id
        WHERE tr.student_id = ? AND tr.test_series_id = ?
    ''', (student_id, test_series_id))
    
    questions = cursor.fetchall()
    conn.close()

    return render_template('center/review_result.html', questions=questions, student_id=student_id, test_series_id=test_series_id)







# ----------------------------- Delete Course ------------------------------------

@app.route('/delete_course/<int:id>')
def delete_course(id):
    if not session.get('admin_logged_in') and not session.get('center_logged_in'):
        return redirect('/')

    conn = sqlite3.connect('lms.db')
    cursor = conn.cursor()

    # Get thumbnail name to delete from static folder
    cursor.execute("SELECT thumbnail FROM courses WHERE id=?", (id,))
    result = cursor.fetchone()
    if result:
        thumbnail_filename = result[0]
        thumbnail_path = os.path.join('static/uploads/courses', thumbnail_filename)
        if os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)

        # Delete course
        cursor.execute("DELETE FROM courses WHERE id=?", (id,))
        conn.commit()

    conn.close()
    return redirect('/view_courses')



# ----------------------------- Manage Course -------------------------

@app.route('/manage_course/<int:course_id>')
def manage_course(course_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM courses WHERE id = ?", (course_id,))
    course = cursor.fetchone()

    cursor.execute("SELECT * FROM modules WHERE course_id = ?", (course_id,))
    modules = cursor.fetchall()

    conn.close()

    return render_template('admin/manage_course.html', course_id=course_id, course_title=course['course_title'], modules=modules)


@app.route('/add_module/<int:course_id>', methods=['POST'])
def add_module(course_id):
    module_title = request.form['module_title']

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO modules (course_id, module_title) VALUES (?, ?)", (course_id, module_title))
    conn.commit()
    conn.close()

    return redirect(f'/manage_course/{course_id}')


@app.route('/delete_module/<int:module_id>', methods=['POST'])
def delete_module(module_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get the course_id first before deleting, to redirect back correctly
    cursor.execute("SELECT course_id FROM modules WHERE id = ?", (module_id,))
    row = cursor.fetchone()
    course_id = row[0] if row else None

    if course_id:
        cursor.execute("DELETE FROM modules WHERE id = ?", (module_id,))
        conn.commit()

    conn.close()
    return redirect(f'/manage_course/{course_id}')






@app.route('/manage_lessons/<int:module_id>')
def manage_lessons(module_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get lessons of the module
    cursor.execute("SELECT * FROM lessons WHERE module_id = ?", (module_id,))
    lessons = cursor.fetchall()

    # Get module title
    cursor.execute("SELECT module_title FROM modules WHERE id = ?", (module_id,))
    module = cursor.fetchone()
    module_title = module['module_title'] if module else "Unknown Module"

    conn.close()
    
    return render_template('admin/manage_lessons.html', module_id=module_id, module_title=module_title, lessons=lessons)

import os
from flask import request, redirect, url_for, flash
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'static/uploads/pdfs'
ALLOWED_EXTENSIONS = {'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/add_lesson', methods=['POST'])
def add_lesson():
    module_id = request.form['module_id']
    lesson_title = request.form['lesson_title']
    video_link = request.form['video_link']
    lesson_id = request.form.get('lesson_id')
    pdf_file = request.files.get('pdf_file')
    pdf_filename = None

    if pdf_file and pdf_file.filename.endswith('.pdf'):
        filename = secure_filename(pdf_file.filename)
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        pdf_file.save(pdf_path)
        pdf_filename = filename

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if lesson_id:  # Update existing
        if pdf_filename:
            cursor.execute("UPDATE lessons SET lesson_title=?, video_link=?, pdf_path=? WHERE id=?",
                           (lesson_title, video_link, pdf_filename, lesson_id))
        else:
            cursor.execute("UPDATE lessons SET lesson_title=?, video_link=? WHERE id=?",
                           (lesson_title, video_link, lesson_id))
    else:  # Add new
        cursor.execute("INSERT INTO lessons (module_id, lesson_title, video_link, pdf_path) VALUES (?, ?, ?, ?)",
                       (module_id, lesson_title, video_link, pdf_filename))

    conn.commit()
    conn.close()
    return redirect(f"/manage_lessons/{module_id}")

 

@app.route('/delete_lesson/<int:lesson_id>', methods=['POST'])
def delete_lesson(lesson_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get module_id and pdf_path before deleting
    cursor.execute("SELECT module_id, pdf_path FROM lessons WHERE id = ?", (lesson_id,))
    row = cursor.fetchone()

    if row:
        module_id, pdf_path = row

        # Delete the PDF file if it exists
        if pdf_path:
            pdf_full_path = os.path.join('static', 'uploads', 'pdfs', pdf_path)
            if os.path.exists(pdf_full_path):
                os.remove(pdf_full_path)

        # Delete lesson from database
        cursor.execute("DELETE FROM lessons WHERE id = ?", (lesson_id,))
        conn.commit()
        conn.close()

        return redirect(f'/manage_lessons/{module_id}')
    else:
        conn.close()
        return "Lesson not found", 404



#================================================================
# ===============================================================

# Center Login
from datetime import datetime, timedelta

@app.route('/center_login', methods=['GET', 'POST'])
def center_login():
    error = None
    if request.method == 'POST':
        center_code = request.form['center_code']
        password = request.form['password']  # Mobile number used as password

        conn = sqlite3.connect('lms.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Fetch center
        cursor.execute("SELECT * FROM centers WHERE center_code = ? AND mobile = ?", (center_code, password))
        center = cursor.fetchone()

        if center:
            # Fetch latest subscription
            cursor.execute("""
                SELECT * FROM subscriptions 
                WHERE center_code = ? 
                ORDER BY start_date DESC 
                LIMIT 1
            """, (center_code,))
            subscription = cursor.fetchone()
            
            if subscription:
                end_date = datetime.strptime(subscription['end_date'], '%Y-%m-%d')
                cutoff_date = end_date - timedelta(days=0)
                today = datetime.today()

                if subscription['status'] != 'Active':
                    error = "Your subscription is not active."
                elif today > cutoff_date:
                    error = "Your subscription has expired. Please contact the Admin."
                else:
                    session['login_type'] = 'center'
                    session['center_code'] = center_code
                    session['center_logged_in'] = True
                    conn.close()
                    return redirect('/center_panel')
            else:
                error = "No subscription found. Please contact the Admin."
        else:
            error = "Invalid Center Code or Mobile Number"

        conn.close()
    return render_template('center/login.html', error=error)










from datetime import datetime, timedelta
import requests

@app.route('/center_panel')
def center_panel():
    if not session.get('center_logged_in'):
        return redirect('/center_login')

    center_code = session.get('center_code')

    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Fetch center details
    cursor.execute("SELECT * FROM centers WHERE center_code = ?", (center_code,))
    center = cursor.fetchone()

    # Fetch subscription info
    cursor.execute("SELECT * FROM subscriptions WHERE center_code = ? ORDER BY id DESC LIMIT 1", (center_code,))
    subscription = cursor.fetchone()

    subscription_warning = ""
    subscription_days_left = 999  # <-- Default high number if no subscription

    if subscription:
        end_date = datetime.strptime(subscription['end_date'], '%Y-%m-%d')
        remaining_days = (end_date - datetime.now()).days
        subscription_days_left = remaining_days
        if remaining_days <= 5:
            subscription_warning = f"Your subscription will expire in {remaining_days} day(s)!"

    conn.close()

    # Optional Weather API
    try:
        weather_info = "Not Available"
        city = "Delhi"
        api_key = "YOUR_OPENWEATHER_API_KEY"
        response = requests.get(
            f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        )
        data = response.json()
        if data.get("main"):
            temp = data["main"]["temp"]
            condition = data["weather"][0]["description"].title()
            weather_info = f"{temp}°C, {condition}"
    except:
        weather_info = "Weather fetch error"

    return render_template('center/center_panel.html',
                           center=center,
                           subscription_warning=subscription_warning,
                           subscription_days_left=subscription_days_left,
                           weather_info=weather_info,
                           current_time=datetime.now().strftime("%d-%b-%Y %I:%M %p"))




from flask import render_template, session, redirect
import sqlite3
from datetime import datetime

@app.route('/center/dashboard')
def center_dashboard():
    if 'center_code' not in session:
        return redirect('/center/login')

    center_code = session.get('center_code')

    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    today = datetime.now().strftime('%Y-%m-%d')

    # Query: Total Students for center
    cursor.execute("SELECT COUNT(*) FROM students WHERE center_code = ?", (center_code,))
    total_students = cursor.fetchone()[0]

    # Query: Total Batches for center
    cursor.execute("SELECT COUNT(*) FROM batches WHERE center_code = ?", (center_code,))
    total_batches = cursor.fetchone()[0]

    # Query: Today's Attendance
    cursor.execute('''
        SELECT COUNT(*) FROM attendance 
        WHERE date = ? 
        AND batch_id IN (SELECT id FROM batches WHERE center_code = ?)
    ''', (today, center_code))
    todays_attendance = cursor.fetchone()[0]

    # Query: Total Courses uploaded by this center
    cursor.execute("SELECT COUNT(*) FROM courses WHERE center_code = ?", (center_code,))
    total_courses = cursor.fetchone()[0]

    # Query: Total Questions in courses uploaded by this center
    cursor.execute('''
        SELECT COUNT(*) FROM questions 
        WHERE course_id IN (SELECT id FROM courses WHERE center_code = ?)
    ''', (center_code,))
    total_questions = cursor.fetchone()[0]

    # Query: Total Test Series created by this center
    cursor.execute("SELECT COUNT(*) FROM test_series WHERE created_by = ?", (center_code,))
    total_test_series = cursor.fetchone()[0]

    conn.close()

    return render_template('center/center_panel_home.html',
                           total_students=total_students,
                           total_batches=total_batches,
                           todays_attendance=todays_attendance,
                           total_courses=total_courses,
                           total_questions=total_questions,
                           total_test_series=total_test_series)








@app.route('/center_logout')
def center_logout():
    session.clear()
    return redirect('/center_login')

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if 'center_code' not in session:
        return redirect('/center_login')

    # ensure upload folder exists
    STD_FOLDER = os.path.join(app.root_path, 'static/uploads/students')
    os.makedirs(STD_FOLDER, exist_ok=True)

    center_code = session['center_code']
    conn = sqlite3.connect('lms.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        student_id = request.form['student_id'].strip()

        # 1) Check for duplicate admission
        cursor.execute("SELECT 1 FROM students WHERE student_id = ?", (student_id,))
        if cursor.fetchone():
            flash("⚠️ Duplicate admission found: this student is already admitted.", "warning")
            conn.close()
            return redirect(url_for('add_student'))

        # 2) Collect form data
        data = {
            'student_id':    student_id,
            'center_code':   center_code,
            'name':          request.form['name'],
            'father_name':   request.form['father_name'],
            'dob':           request.form['dob'],
            'gender':        request.form['gender'],
            'mobile':        request.form['mobile'],
            'alt_mobile':    request.form['alt_mobile'],
            'email':         request.form['email'],
            'address':       request.form['address'],
            'city':          request.form['city'],
            'pin_code':      request.form['pin_code'],
            'state':         request.form['state'],
            'qualification': request.form['qualification'],
            'passing_year':  request.form['passing_year'],
            'school':        request.form['school'],
            'board':         request.form['board'],
            'admission_date':request.form['admission_date'],
            'photo':         '',
            'status':        request.form['status']
        }

        # 3) Handle photo upload
        photo = request.files.get('photo')
        if photo and photo.filename:
            ext = photo.filename.rsplit('.', 1)[-1]
            filename = secure_filename(f"{student_id}.{ext}")
            photo_path = os.path.join(STD_FOLDER, filename)
            photo.save(photo_path)
            data['photo'] = os.path.join('uploads/students', filename)

        # 4) Insert into DB
        cursor.execute('''
            INSERT INTO students (
                student_id, center_code, name, father_name, dob, gender, mobile, alt_mobile,
                email, address, city, pin_code, state, qualification, passing_year,
                school, board, admission_date, photo, status
            ) VALUES (
                :student_id, :center_code, :name, :father_name, :dob, :gender, :mobile, :alt_mobile,
                :email, :address, :city, :pin_code, :state, :qualification, :passing_year,
                :school, :board, :admission_date, :photo, :status
            )
        ''', data)
        conn.commit()
        conn.close()

        flash("✅ Student added successfully.", "success")
        return redirect(url_for('add_student'))

    # GET
    conn.close()
    return render_template('center/add_student.html', center_code=center_code)


from flask import jsonify

@app.route('/check_student_id')
def check_student_id():
    student_id = request.args.get('student_id', '').strip()
    conn = sqlite3.connect('lms.db')
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM students WHERE student_id = ?", (student_id,))
    exists = cursor.fetchone() is not None
    conn.close()
    return jsonify({ 'exists': exists })








import io, os, sqlite3
import pandas as pd
from flask import Flask, send_file, render_template, request, redirect, session, flash


# Where to store uploaded excels
UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads', 'excel_files')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)



@app.route('/download_sample')
def download_sample():
    # Only the five mandatory columns
    cols = ['student_id','name','mobile','email','admission_date']
    df = pd.DataFrame(columns=cols)

    # Write to an in‑memory Excel file
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)

    return send_file(
        output,
        download_name='bulk_admission_sample.xlsx',
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@app.route('/bulk_admission', methods=['GET', 'POST'])
def bulk_admission():
    if 'center_code' not in session:
        return redirect('/center_login')

    center_code   = session['center_code']
    uploaded_data = []
    added = skipped = 0

    if request.method == 'POST':
        file = request.files.get('excel_file')
        if not file or not file.filename.lower().endswith(('.xlsx', '.xls')):
            flash("❌ Please upload a valid Excel file (.xls/.xlsx)", "danger")
            return redirect(request.url)

        path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(path)

        try:
            df = pd.read_excel(path)
            df.columns = [c.strip().lower() for c in df.columns]

            # our five required fields
            mandatory = ['student_id','name','mobile','email','admission_date']

            # normalize the date column
            df['admission_date'] = pd.to_datetime(
                df['admission_date'], errors='coerce'
            ).dt.strftime('%Y-%m-%d')

            conn = sqlite3.connect('lms.db')
            cursor = conn.cursor()

            for _, row in df.iterrows():
                # skip if any mandatory is missing/blank
                if any(
                    pd.isna(row.get(col)) or str(row.get(col)).strip()=='' 
                    for col in mandatory
                ):
                    skipped += 1
                    continue

                # cast & strip
                sid  = str(row['student_id']).strip()
                name = str(row['name']).strip()
                mob  = str(row['mobile']).strip()
                mail = str(row['email']).strip()
                adm  = str(row['admission_date']).strip()

                # skip duplicate student_id
                cursor.execute(
                    "SELECT 1 FROM students WHERE student_id = ?", (sid,)
                )
                if cursor.fetchone():
                    skipped += 1
                    continue

                # build the 21‑element tuple for your table
                data = (
                    sid,               # student_id
                    center_code,       # center_code
                    '',                # batch_id
                    name,              # name
                    '',                # father_name
                    '',                # dob
                    '',                # gender
                    mob,               # mobile
                    '',                # alt_mobile
                    mail,              # email
                    '',                # address
                    '',                # city
                    '',                # pin_code
                    '',                # state
                    '',                # qualification
                    '',                # passing_year
                    '',                # school
                    '',                # board
                    adm,               # admission_date
                    '',                # photo
                    'Active'           # status
                )

                # 21 columns → 21 placeholders
                cursor.execute('''
                  INSERT INTO students (
                    student_id, center_code, batch_id, name, father_name, dob, gender, mobile,
                    alt_mobile, email, address, city, pin_code, state, qualification,
                    passing_year, school, board, admission_date, photo, status
                  ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ''', data)

                added += 1
                uploaded_data.append({
                    'student_id': sid,
                    'name':       name,
                    'mobile':     mob,
                    'email':      mail,
                    'admission_date': adm
                })

            conn.commit()
            conn.close()

            flash(f"✅ {added} added. ❌ {skipped} skipped.", "success")

        except Exception as e:
            flash(f"❌ Error processing file: {e}", "danger")

    return render_template('center/add_student.html',
                           uploaded_data=uploaded_data)





@app.route('/view_students', methods=['GET', 'POST'])
def view_students():
    if not session.get('center_logged_in'):
        return redirect('/center_login')

    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    search_term = request.form.get('search_term', '').strip()
    center_code = session.get('center_code')

    if search_term:
        cursor.execute('''SELECT * FROM students 
                          WHERE center_code = ? AND 
                          (student_id LIKE ? OR name LIKE ? OR mobile LIKE ?)''',
                       (center_code, f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
    else:
        cursor.execute("SELECT * FROM students WHERE center_code = ?", (center_code,))

    students = cursor.fetchall()
    conn.close()

    return render_template('center/view_students.html', students=students)



from flask import send_file, session, redirect, flash
import pandas as pd
import os

@app.route('/center/export_students')
def export_students():
    if not session.get('center_logged_in'):
        flash("Please login first!")
        return redirect('/center_login')

    center_code = session.get('center_code')
    conn = sqlite3.connect('lms.db')
    query = "SELECT student_id, name, father_name, dob, gender, mobile, email, city, status, admission_date FROM students WHERE center_code = ?"
    df = pd.read_sql_query(query, conn, params=(center_code,))
    conn.close()

    export_folder = os.path.join('static', 'exports')
    os.makedirs(export_folder, exist_ok=True)
    file_path = os.path.join(export_folder, f"{center_code}_students.xlsx")
    df.to_excel(file_path, index=False)

    return send_file(file_path, as_attachment=True)


import os
from flask import flash, redirect, url_for
from werkzeug.utils import secure_filename

@app.route('/center/delete_student/<int:id>')
def delete_student(id):
    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Step 1: Get the photo filename of the student
    cursor.execute("SELECT photo FROM students WHERE id = ?", (id,))
    student = cursor.fetchone()

    if student and student['photo']:
        # Step 2: Construct full file path
        photo_path = os.path.join('static', 'uploads', 'students', student['photo'])

        # Step 3: Delete file if it exists
        if os.path.exists(photo_path):
            try:
                os.remove(photo_path)
            except Exception as e:
                print(f"Error deleting file: {e}")

    # Step 4: Delete the student record from database
    cursor.execute("DELETE FROM students WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    flash("Student and photo deleted successfully!")
    return redirect('/view_students')




@app.route('/edit_student/<int:student_id>')
def edit_student(student_id):
    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
    student = cursor.fetchone()
    conn.close()

    if not student:
        return "Student not found", 404

    return render_template('center/edit_student.html', student=student)


@app.route('/update_student/<int:student_id>', methods=['POST'])
def update_student(student_id):
    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return "Student not found", 404

    student = dict(row)

    name = request.form['name']
    father_name = request.form['father_name']
    dob = request.form['dob']
    mobile = request.form['mobile']
    alt_mobile = request.form['alt_mobile']
    email = request.form['email']
    gender = request.form['gender']
    address = request.form['address']
    city = request.form['city']
    pin_code = request.form['pin_code']
    state = request.form['state']
    qualification = request.form['qualification']
    passing_year = request.form['passing_year']
    school = request.form['school']
    board = request.form['board']
    admission_date = request.form['admission_date']
    status = request.form['status']

    photo = request.files.get('photo')
    photo_filename = student.get('photo') or ''
    STD_FOLDER = os.path.join(app.root_path, 'static/uploads/students')
    os.makedirs(STD_FOLDER, exist_ok=True)

    if photo and photo.filename:
        ext = photo.filename.rsplit('.', 1)[-1]
        filename = secure_filename(f"{student['student_id']}.{ext}")
        photo_path = os.path.join(STD_FOLDER, filename)
        photo.save(photo_path)
        photo_filename = os.path.join('uploads/students', filename)

    cursor.execute("""
        UPDATE students SET name=?, father_name=?, dob=?, mobile=?, alt_mobile=?,
        email=?, gender=?, address=?, city=?, pin_code=?, state=?, qualification=?,
        passing_year=?, school=?, board=?, admission_date=?, status=?, photo=?
        WHERE id=?
    """, (
        name, father_name, dob, mobile, alt_mobile, email, gender, address, city, pin_code,
        state, qualification, passing_year, school, board, admission_date, status, photo_filename, student_id
    ))

    conn.commit()
    conn.close()

    return redirect(url_for('view_students'))



@app.route('/center/add_payment', methods=['GET', 'POST'])
def add_payment():
    if 'center_code' not in session:
        return redirect('/center_login')

    center_code = session['center_code']
    msg = ""

    if request.method == 'POST':
        student_id = request.form['student_id']
        payment_date = request.form['payment_date']
        actual_payment_date = request.form['actual_payment_date']
        payment_amount = float(request.form['payment_amount'])
        payment_mode = request.form['payment_mode']
        payment_status = request.form['payment_status']
        installment_name = request.form['installment_name']
        remarks = request.form['remarks']

        # Get student info
        conn = sqlite3.connect('lms.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT batch_id, center_code FROM students WHERE student_id=?", (student_id,))
        student = cursor.fetchone()

        if student:
            batch_id, center_code = student

            # Get last balance
            cursor.execute("SELECT balance_amount FROM payments WHERE student_id=? ORDER BY id DESC LIMIT 1", (student_id,))
            last_payment = cursor.fetchone()

            if last_payment:
                last_balance = last_payment[0]
                new_balance = last_balance - payment_amount
            else:
                # First payment – take balance from form
                new_balance = float(request.form['balance_amount']) - payment_amount

            # Insert payment
            cursor.execute('''INSERT INTO payments (student_id, center_code, batch_id, payment_date, actual_payment_date,
                              payment_amount, balance_amount, payment_mode, payment_status, installment_name, remarks)
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                           (student_id, center_code, batch_id, payment_date, actual_payment_date, payment_amount,
                            new_balance, payment_mode, payment_status, installment_name, remarks))
            conn.commit()
            msg = "💰 Payment recorded successfully."
        else:
            msg = "❌ Invalid Student ID."

    return render_template('center/add_payment.html', msg=msg)




from flask import jsonify, request

@app.route('/get_student_details', methods=['POST'])
def get_student_details():
    student_id = request.form['student_id'].strip()
    center_code = session.get('center_code')

    conn = sqlite3.connect('lms.db')
    cursor = conn.cursor()

    # Get student basic info
    cursor.execute("SELECT name, batch_id, admission_date FROM students WHERE student_id = ? AND center_code = ?", (student_id, center_code))
    student = cursor.fetchone()

    # Get last balance from payments
    cursor.execute("SELECT balance_amount FROM payments WHERE student_id = ? ORDER BY id DESC LIMIT 1", (student_id,))
    last_payment = cursor.fetchone()

    conn.close()

    if student:
        return jsonify({
            'status': 'success',
            'name': student[0],
            'batch_id': student[1],
            'admission_date': student[2],
            'balance_amount': last_payment[0] if last_payment else None
        })
    else:
        return jsonify({'status': 'fail'})

# ------------------------- Payment Slip ----------------------------------

@app.route('/payment_slip/<int:payment_id>')
def payment_slip(payment_id):
    if 'center_code' not in session:
        return redirect('/center_login')

    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT payments.*, students.name, students.student_id, students.batch_id, students.center_code, batches.batch_name
        FROM payments
        JOIN students ON payments.student_id = students.student_id
        JOIN batches ON students.batch_id = batches.id
        WHERE payments.id = ?
    ''', (payment_id,))
    payment = cursor.fetchone()

    if not payment:
        conn.close()
        return "Invalid payment ID"

    # Fetch center name and center_code from centers table
    cursor.execute('SELECT * FROM centers WHERE center_code = ?', (payment['center_code'],))
    center = cursor.fetchone()

    conn.close()
    return render_template("center/payment_slip.html", payment=payment, center=center)



@app.route('/student_payment_history/<student_id>')
def student_payment_history(student_id):
    if 'center_code' not in session:
        return redirect('/center_login')

    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1) Fetch student
    cur.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
    student = cur.fetchone()
    if not student:
        conn.close()
        flash("❌ Student not found.", "danger")
        return redirect(url_for('dues'))

    # 2) Fetch center info
    cur.execute("""
      SELECT center_name, center_code 
      FROM centers 
      WHERE center_code = ?
    """, (student['center_code'],))
    center = cur.fetchone()

    # 3) Fetch all payments (newest first)
    cur.execute("""
      SELECT * 
      FROM payments 
      WHERE student_id = ? 
      ORDER BY payment_date DESC
    """, (student_id,))
    payments = cur.fetchall()
    conn.close()

    # 4) Calculate dues
    due_months = 0
    try:
        adm = date.fromisoformat(student['admission_date'])
        today = date.today()
        months_since = (today.year - adm.year) * 12 + (today.month - adm.month) + 1
        paid_count   = len(payments)
        due_months   = max(0, months_since - paid_count)
    except Exception:
        # if admission_date malformed, treat no dues
        due_months = 0

    # 5) Render page
    return render_template(
        "student/student_payment_history.html",
        student=student,
        center=center,
        payments=payments,
        due_months=due_months
    )













# ------------------------ Center Payment ---------------------------------

from flask import render_template, request, send_file
import csv
from io import StringIO
from datetime import datetime

@app.route('/center/view_payments', methods=['GET', 'POST'])
def view_payments():
    if 'center_code' not in session:
        return redirect('/center_login')

    center_code = session['center_code']
    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    payment_mode = request.form.get('payment_mode')
    search_term = request.form.get('search_term')
    download = request.form.get('download')

    # Base query with JOIN
    query = '''
        SELECT payments.*, students.name AS student_name
        FROM payments
        JOIN students ON payments.student_id = students.student_id
        WHERE payments.center_code = ?
    '''
    params = [center_code]

    # Filter by date range
    if start_date and end_date:
        query += " AND date(payments.payment_date) BETWEEN ? AND ?"
        params.extend([start_date, end_date])

    # Filter by payment mode
    if payment_mode and payment_mode != "All":
        query += " AND payments.payment_mode = ?"
        params.append(payment_mode)

    # Search by student ID or name
    if search_term:
        query += " AND (students.student_id LIKE ? OR students.name LIKE ?)"
        like_term = f"%{search_term}%"
        params.extend([like_term, like_term])

    query += " ORDER BY payments.payment_date DESC"

    cursor.execute(query, params)
    payments = cursor.fetchall()

    # Total collection
    total_collection = sum([row['payment_amount'] for row in payments])

    return render_template("center/View_payments.html",
                           payments=payments,
                           total_collection=total_collection,
                           start_date=start_date,
                           end_date=end_date,
                           payment_mode=payment_mode,
                           search_term=search_term)







    if download == "csv":
        # Export to CSV
        si = StringIO()
        cw = csv.writer(si)
        cw.writerow(['Student ID', 'Batch ID', 'Payment Date', 'Payment Amount', 'Mode', 'Status', 'Installment', 'Remarks'])

        for row in payments:
            cw.writerow([
                row['student_id'], row['batch_id'], row['payment_date'],
                row['payment_amount'], row['payment_mode'],
                row['payment_status'], row['installment_name'], row['remarks']
            ])

        # Encode to bytes and send
        mem = BytesIO()
        mem.write(si.getvalue().encode('utf-8'))
        mem.seek(0)

        return send_file(
            mem,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'payments_{datetime.now().date()}.csv'
        )


    return render_template('center/view_payments.html',
                           payments=payments,
                           total_collection=total_collection,
                           start_date=start_date,
                           end_date=end_date,
                           payment_mode=payment_mode)



@app.route('/edit_payment/<int:payment_id>', methods=['GET', 'POST'])
def edit_payment(payment_id):
    if 'center_code' not in session:
        return redirect('/center_login')

    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Fetch payment record
    cursor.execute("SELECT * FROM payments WHERE id = ?", (payment_id,))
    payment = cursor.fetchone()

    if not payment:
        conn.close()
        return "Payment not found", 404

    student_id = payment['student_id']

    if request.method == 'POST':
        payment_date = request.form['payment_date']
        actual_payment_date = request.form['actual_payment_date']
        payment_amount = float(request.form['payment_amount'])
        payment_mode = request.form['payment_mode']
        payment_status = request.form['payment_status']
        installment_name = request.form['installment_name']
        remarks = request.form['remarks']

        # Get latest balance before this payment
        cursor.execute("""
            SELECT balance_amount FROM payments 
            WHERE student_id = ? AND id != ? 
            ORDER BY id DESC LIMIT 1
        """, (student_id, payment_id))
        previous_payment = cursor.fetchone()
        previous_balance = previous_payment['balance_amount'] if previous_payment else 0

        new_balance = previous_balance - payment_amount

        # Update payment
        cursor.execute('''
            UPDATE payments SET 
                payment_date = ?, 
                actual_payment_date = ?, 
                payment_amount = ?, 
                payment_mode = ?, 
                payment_status = ?, 
                installment_name = ?, 
                remarks = ?, 
                balance_amount = ?
            WHERE id = ?
        ''', (
            payment_date,
            actual_payment_date,
            payment_amount,
            payment_mode,
            payment_status,
            installment_name,
            remarks,
            new_balance,
            payment_id
        ))

        conn.commit()
        conn.close()
        return redirect('/center/view_payments')

    conn.close()
    return render_template('center/edit_payment.html', payment=payment)



@app.route('/delete_payment/<int:payment_id>')
def delete_payment(payment_id):
    if 'center_code' not in session:
        return redirect('/center_login')

    conn = sqlite3.connect('lms.db')
    cursor = conn.cursor()

    # Optional: fetch student_id if you want to update balances after deletion
    cursor.execute("SELECT student_id FROM payments WHERE id = ?", (payment_id,))
    payment = cursor.fetchone()

    if not payment:
        conn.close()
        return "Payment not found", 404

    cursor.execute("DELETE FROM payments WHERE id = ?", (payment_id,))
    conn.commit()
    conn.close()

    return redirect('/center/view_payments')




# ------------------------ Diues Payment ---------------------------

@app.route('/center/dues', methods=['GET'])
def dues():
    if 'center_code' not in session:
        return redirect('/center_login')

    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
      SELECT student_id, name, admission_date
      FROM students
      WHERE center_code = ?
    """, (session['center_code'],))
    students = cur.fetchall()
    today = date.today()

    dues_list = []
    for r in students:
        try:
            adm = date.fromisoformat(r['admission_date'])
        except:
            continue

        months_since = (today.year - adm.year) * 12 + (today.month - adm.month) + 1

        cur.execute("SELECT COUNT(*) FROM payments WHERE student_id = ?", (r['student_id'],))
        paid_count = cur.fetchone()[0]

        due_months = months_since - paid_count
        if due_months > 0:
            dues_list.append({
                'student_id':     r['student_id'],
                'name':           r['name'],
                'admission_date': r['admission_date'],
                'due_months':     due_months
            })

    conn.close()
    return render_template('center/dues.html', dues_list=dues_list)



@app.route('/center/clear_due/<student_id>', methods=['POST'])
def clear_due(student_id):
    if 'center_code' not in session:
        return redirect('/center_login')

    conn = sqlite3.connect('lms.db')
    cur  = conn.cursor()

    # Get last balance if any
    cur.execute("""
      SELECT balance_amount
      FROM payments
      WHERE student_id = ?
      ORDER BY id DESC LIMIT 1
    """, (student_id,))
    last = cur.fetchone()
    last_balance = last[0] if last else 0.0

    today_str = date.today().isoformat()

    # Insert exactly ONE zero‑amount payment to clear one month
    cur.execute("""
      INSERT INTO payments (
        student_id, center_code, batch_id,
        payment_date, actual_payment_date,
        payment_amount, balance_amount,
        payment_mode, payment_status,
        installment_name, remarks
      ) VALUES (
        ?, ?, '',
        ?, ?,
        0.0, ?,
        'Clear Due', 'Success',
        'Clear Dues', 'Waived one month fee'
      )
    """, (
      student_id,
      session['center_code'],
      today_str,
      today_str,
      last_balance
    ))

    conn.commit()
    conn.close()

    flash("✅ One month of dues cleared.", "success")
    return redirect(url_for('dues'))

# ------------------------ Adjust Payment --------------------------------

@app.route('/center/manage_adjustment', methods=['GET', 'POST'])
def manage_adjustment():
    if 'center_code' not in session:
        return redirect('/center_login')
    center_code = session['center_code']

    student = None
    last_balance = 0.0
    adjustments = []
    total_adjusted = 0.0

    if request.method == 'POST' and 'adjust_amount' in request.form:
        sid      = request.form['student_id']
        amt      = float(request.form['adjust_amount'])
        adj_date = request.form['adjust_date']
        ref_by   = request.form['reference_by']
        adj_for  = request.form['adjust_for']
        remarks  = request.form['remarks']

        conn = sqlite3.connect('lms.db')
        cur  = conn.cursor()

        # 1) Insert adjustment, capture its ID
        cur.execute("""
          INSERT INTO adjustments (
            student_id, center_code, adjust_date,
            amount, reference_by, adjust_for, remarks
          ) VALUES (?,?,?,?,?,?,?)
        """, (sid, center_code, adj_date, amt, ref_by, adj_for, remarks))
        adj_id = cur.lastrowid

        # 2) Fetch batch_id & last balance
        cur.execute("""
          SELECT batch_id, balance_amount
          FROM payments
          WHERE student_id=? ORDER BY id DESC LIMIT 1
        """, (sid,))
        row = cur.fetchone()
        batch_id, last_balance = (row[0], row[1]) if row else ('', 0.0)

        new_balance = last_balance - amt

        # 3) Record in payments with adjustment_id
        cur.execute("""
          INSERT INTO payments (
            student_id, center_code, batch_id,
            payment_date, actual_payment_date,
            payment_amount, balance_amount,
            payment_mode, payment_status,
            installment_name, remarks,
            adjustment_id
          ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
          sid, center_code, batch_id,
          adj_date, adj_date,
          amt, new_balance,
          'Adjustment', 'Success',
          adj_for,
          f"{remarks} (Ref: {ref_by})",
          adj_id
        ))

        conn.commit()
        conn.close()
        flash(f"✅ Adjusted ₹{amt:.2f}; new balance ₹{new_balance:.2f}.", "success")

    lookup = request.values.get('student_id')
    if lookup:
        conn = sqlite3.connect('lms.db')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # load student
        cur.execute("""
          SELECT student_id, batch_id, admission_date
          FROM students
          WHERE student_id=? AND center_code=?
        """, (lookup, center_code))
        student = cur.fetchone()

        if student:
            # last balance
            cur.execute("""
              SELECT balance_amount
              FROM payments
              WHERE student_id=? ORDER BY id DESC LIMIT 1
            """, (lookup,))
            r = cur.fetchone()
            last_balance = r['balance_amount'] if r else 0.0

            # all adjustments
            cur.execute("""
              SELECT * FROM adjustments
              WHERE student_id=? ORDER BY adjust_date DESC
            """, (lookup,))
            adjustments = cur.fetchall()
            total_adjusted = sum(a['amount'] for a in adjustments)

        conn.close()

    return render_template(
      'center/manage_adjustment.html',
      student=student,
      last_balance=last_balance,
      adjustments=adjustments,
      total_adjusted=total_adjusted,
      effective_balance=last_balance - total_adjusted,
      today_str=date.today().isoformat()
    )



@app.route('/center/delete_adjustment/<int:adj_id>', methods=['POST'])
def delete_adjustment(adj_id):
    if 'center_code' not in session:
        return redirect('/center_login')

    conn = sqlite3.connect('lms.db')
    cur  = conn.cursor()

    # Find the adjustment record
    cur.execute("SELECT student_id, amount FROM adjustments WHERE id=?", (adj_id,))
    row = cur.fetchone()
    if not row:
        flash("❌ Adjustment not found.", "danger")
        conn.close()
        return redirect(url_for('manage_adjustment'))

    sid, amt = row

    # 1) Delete the adjustment
    cur.execute("DELETE FROM adjustments WHERE id=?", (adj_id,))

    # 2) Delete the linked payment
    cur.execute("""
      DELETE FROM payments
      WHERE adjustment_id = ?
    """, (adj_id,))

    conn.commit()
    conn.close()
    flash(f"🗑️ Deleted adjustment of ₹{amt:.2f}. Balance restored.", "success")
    return redirect(url_for('manage_adjustment', student_id=sid))






# ------------------------ Manage Batches ----------------------------------


# Generate Batch Code
def generate_batch_code():
    conn = sqlite3.connect('lms.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM batches")
    count = cursor.fetchone()[0] + 1
    conn.close()
    return f"BT-{str(count).zfill(3)}"

@app.route('/center/manage_batches', methods=['GET', 'POST'])
def manage_batches():
    if not session.get('center_logged_in'):
        return redirect('/center_login')

    center_code = session['center_code']
    batch_id = request.args.get('edit')
    editing_batch = None

    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Handle Create or Update
    if request.method == 'POST':
        batch_name = request.form['batch_name']
        batch_time = request.form['batch_time']
        duration = request.form.get('duration')
        start_date = request.form['start_date']
        status = request.form['status']

        if request.form.get('batch_id'):  # Update
            batch_id = request.form['batch_id']
            cursor.execute('''
                UPDATE batches SET batch_name=?, batch_time=?, duration=?, start_date=?, status=?
                WHERE id=? AND center_code=?
            ''', (batch_name, batch_time, duration, start_date, status, batch_id, center_code))
        else:  # Insert
            batch_code = generate_batch_code()
            cursor.execute('''
                INSERT INTO batches (batch_code, batch_name, batch_time, duration, start_date, status, center_code)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (batch_code, batch_name, batch_time, duration, start_date, status, center_code))
        conn.commit()

        return redirect('/center/manage_batches')

    # Fetch editing batch
    if batch_id:
        cursor.execute("SELECT * FROM batches WHERE id=? AND center_code=?", (batch_id, center_code))
        editing_batch = cursor.fetchone()

    # Fetch all batches with student count
    cursor.execute('''
        SELECT b.*, 
        (SELECT COUNT(*) FROM students WHERE batch_id = b.id) as student_count
        FROM batches b 
        WHERE b.center_code = ?
        ORDER BY b.id DESC
    ''', (center_code,))

    batches = cursor.fetchall()
    conn.close()

    return render_template('center/manage_batches.html', batches=batches, editing_batch=editing_batch)



@app.route('/center/delete_batch/<int:batch_id>')
def delete_batch(batch_id):
    if not session.get('center_logged_in'):
        return redirect('/center_login')

    center_code = session['center_code']
    conn = sqlite3.connect('lms.db')
    cursor = conn.cursor()

    # Optional: delete related students if needed
    cursor.execute("DELETE FROM batch_students WHERE batch_id=?", (batch_id,))
    cursor.execute("DELETE FROM batches WHERE id=? AND center_code=?", (batch_id, center_code))
    conn.commit()
    conn.close()
    return redirect('/center/manage_batches')





# ------------------------------ Batch Management ---------------------------

@app.route('/center/add_students_to_batch/<string:batch_id>', methods=['GET', 'POST'])
def add_students_to_batch(batch_id):
    if not session.get('center_logged_in'):
        return redirect('/center_login')

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get batch info
    cursor.execute("SELECT * FROM batches WHERE batch_code = ?", (batch_id,))
    batch = cursor.fetchone()

    messages = []
    valid_students = []

    if request.method == 'POST':
        ids_input = request.form['student_ids']
        student_ids = [i.strip() for i in ids_input.split(',') if i.strip()]

        for sid in student_ids:
            cursor.execute("SELECT * FROM students WHERE student_id = ?", (sid,))
            student = cursor.fetchone()

            if not student:
                messages.append(f"{sid} - Invalid ID")
            elif student['batch_id'] and student['batch_id'] != batch_id:
                messages.append(f"{sid} - Already in batch {student['batch_id']}")
            else:
                cursor.execute("UPDATE students SET batch_id = ? WHERE student_id = ?", (batch_id, sid))
                valid_students.append(sid)

        conn.commit()

    # Students in this batch
    cursor.execute("SELECT * FROM students WHERE batch_id = ?", (batch_id,))
    batch_students = cursor.fetchall()

    conn.close()

    return render_template('center/add_students_to_batch.html', batch=batch,
                           batch_students=batch_students, messages=messages, added_students=valid_students)



@app.route('/center/remove_from_batch/<string:student_id>')
def remove_from_batch(student_id):
    if not session.get('center_logged_in'):
        return redirect('/center_login')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE students SET batch_id = NULL WHERE student_id = ?", (student_id,))
    conn.commit()
    conn.close()

    return redirect(request.referrer or '/center/manage_batches')


@app.route('/center/search_student')
def search_student():
    query = request.args.get('q', '')
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE student_id LIKE ?", ('%' + query + '%',))
    results = cursor.fetchall()
    conn.close()
    return render_template('center/search_student.html', results=results)



# --------------------------------- Attendance Section ------------------------

@app.route('/center/attendance', methods=['GET'])
def attendance():
    if 'center_logged_in' not in session:
        return redirect('/center_login')

    center_code = session['center_code']
    selected_batch_id = request.args.get('batch_id')
    selected_date = request.args.get('date')

    today = datetime.today().strftime('%Y-%m-%d')
    if not selected_date:
        selected_date = today

    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all batches for dropdown
    cursor.execute("SELECT * FROM batches WHERE center_code = ?", (center_code,))
    batches = cursor.fetchall()

    attendance_data = []
    if selected_batch_id:
        # Get students in this batch
        cursor.execute('''
            SELECT s.id as student_id, s.student_id as student_code, s.name,
                   a.status
            FROM students s
            LEFT JOIN attendance a 
            ON s.id = a.student_id AND a.batch_id = ? AND a.date = ?
            WHERE s.batch_id = ? AND s.center_code = ?
        ''', (selected_batch_id, selected_date, selected_batch_id, center_code))
        attendance_data = cursor.fetchall()

    conn.close()

    return render_template("center/attendance.html",
                           batches=batches,
                           attendance_data=attendance_data,
                           selected_batch_id=selected_batch_id,
                           selected_date=selected_date,
                           today=today)



@app.route('/center/save_attendance', methods=['POST'])
def save_attendance():
    if 'center_logged_in' not in session:
        return redirect('/center_login')

    center_code = session['center_code']
    batch_id = request.form['batch_id']
    date = request.form['date']
    present_ids = request.form.getlist('present[]')  # list of student IDs marked as present

    conn = sqlite3.connect('lms.db')
    cursor = conn.cursor()

    # Get all students in the selected batch
    cursor.execute("SELECT id FROM students WHERE batch_id = ? AND center_code = ?", (batch_id, center_code))
    student_ids = [str(row[0]) for row in cursor.fetchall()]

    for sid in student_ids:
        status = 'Present' if sid in present_ids else 'Absent'
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO attendance (student_id, batch_id, date, status)
                VALUES (?, ?, ?, ?)
            ''', (sid, batch_id, date, status))
        except Exception as e:
            print("Error inserting:", e)

    conn.commit()
    conn.close()
    
    flash("Attendance Saved Successfully", "success")
    return redirect(f"/center/attendance?batch_id={batch_id}&date={date}")





from calendar import monthrange
from datetime import datetime

@app.route('/center/view_attendance_report', methods=['GET'])
def view_attendance_report():
    if not session.get('center_logged_in'):
        return redirect('/center_login')

    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    center_code = session['center_code']
    cursor.execute("SELECT * FROM batches WHERE center_code=?", (center_code,))
    batches = cursor.fetchall()

    selected_batch_id = request.args.get('batch_id')
    selected_month = request.args.get('month')  # format YYYY-MM

    students = []
    attendance_data = {}
    days_in_month = []

    if selected_batch_id and selected_month:
        year, month = map(int, selected_month.split('-'))
        num_days = monthrange(year, month)[1]
        days_in_month = [str(day) for day in range(1, num_days+1)]

        # Get all students
        cursor.execute("SELECT id, name, student_id FROM students WHERE batch_id=?", (selected_batch_id,))

        students = cursor.fetchall()

        # Fetch all attendance in month
        start_date = f"{selected_month}-01"
        end_date = f"{selected_month}-{num_days:02d}"
        cursor.execute("""
            SELECT student_id, date, status FROM attendance 
            WHERE batch_id = ? AND date BETWEEN ? AND ?
        """, (selected_batch_id, start_date, end_date))
        rows = cursor.fetchall()

        # Organize attendance by student_id and date
        for row in rows:
            student_id = row['student_id']
            date = row['date']
            status = row['status']
            if student_id not in attendance_data:
                attendance_data[student_id] = {}
            attendance_data[student_id][date] = status

    conn.close()

    return render_template('center/view_attendance_report.html',
                           batches=batches,
                           selected_batch_id=selected_batch_id,
                           selected_month=selected_month,
                           selected_year=year if selected_month else '',
                           selected_month_num=month if selected_month else '',
                           students=students,
                           days_in_month=days_in_month,
                           attendance=attendance_data)



import csv
from io import BytesIO, StringIO

from flask import Response

@app.route('/center/export_attendance_csv', methods=['POST'])
def export_attendance_csv():
    if 'center_logged_in' not in session:
        return redirect('/center_login')

    batch_id = request.form['batch_id']
    month = request.form['month']
    year, month_num = map(int, month.split('-'))
    num_days = monthrange(year, month_num)[1]

    conn = sqlite3.connect('lms.db')
    cursor = conn.cursor()

    # Get students
    cursor.execute("SELECT id, student_id, name FROM students WHERE batch_id=?", (batch_id,))
    students = cursor.fetchall()

    # Get attendance
    start_date = f"{month}-01"
    end_date = f"{month}-{num_days:02d}"
    cursor.execute("""
        SELECT student_id, date, status FROM attendance 
        WHERE batch_id = ? AND date BETWEEN ? AND ?
    """, (batch_id, start_date, end_date))
    records = cursor.fetchall()

    attendance_dict = {}
    for sid, date, status in records:
        if sid not in attendance_dict:
            attendance_dict[sid] = {}
        attendance_dict[sid][date] = status

    # Generate CSV
    output = StringIO()
    writer = csv.writer(output)

    # Header row
    header = ['Student ID', 'Name'] + [str(day) for day in range(1, num_days+1)]
    writer.writerow(header)

    for student in students:
        row = [student[1], student[2]]  # student_code, name
        sid = student[0]
        for d in range(1, num_days+1):
            date = f"{month}-{d:02d}"
            status = attendance_dict.get(sid, {}).get(date, '-')
            row.append(status)
        writer.writerow(row)

    output.seek(0)
    return Response(output.getvalue(),
                    mimetype='text/csv',
                    headers={"Content-Disposition": f"attachment;filename=attendance_{month}.csv"})


# ---------------------------- Assign Course to Batch ---------------------
@app.route('/assign_course_to_batch', methods=['GET', 'POST'])
def assign_course_to_batch():
    if 'center_code' not in session:
        return redirect('/center_login')

    center_code = session['center_code']
    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Fetch batches for this center
    cursor.execute("SELECT * FROM batches WHERE center_code=?", (center_code,))
    batches = cursor.fetchall()

    # Fetch courses (admin + center)
    cursor.execute("SELECT * FROM courses WHERE uploaded_by='admin' OR center_code=?", (center_code,))
    courses = cursor.fetchall()

    message = ""

    # Handle course assignment
    if request.method == 'POST' and 'batch_id' in request.form:
        batch_id = request.form['batch_id']
        course_id = request.form['course_id']
        today = datetime.now().strftime("%Y-%m-%d")

        cursor.execute("SELECT id FROM students WHERE batch_id=?", (batch_id,))
        students = cursor.fetchall()

        count = 0
        for student in students:
            student_id = student['id']
            cursor.execute("SELECT * FROM student_courses WHERE student_id=? AND course_id=?", (student_id, course_id))
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO student_courses (student_id, course_id, assigned_date) VALUES (?, ?, ?)",
                    (student_id, course_id, today)
                )
                count += 1

        conn.commit()
        message = f"{count} student(s) enrolled successfully in the course."

    # Handle course removal
    if request.method == 'POST' and 'remove' in request.form:
        batch_id = request.form['remove_batch_id']
        course_id = request.form['remove_course_id']

        cursor.execute("SELECT id FROM students WHERE batch_id=?", (batch_id,))
        students = cursor.fetchall()

        removed_count = 0
        for student in students:
            student_id = student['id']
            cursor.execute("DELETE FROM student_courses WHERE student_id=? AND course_id=?", (student_id, course_id))
            removed_count += cursor.rowcount

        conn.commit()
        message = f"{removed_count} enrollment(s) removed from the course."

    # Get existing batch-course assignments
    cursor.execute('''
        SELECT DISTINCT b.id AS batch_id, b.batch_code, b.batch_name,
                        c.id AS course_id, c.course_code, c.course_title
        FROM student_courses sc
        JOIN students s ON sc.student_id = s.id
        JOIN batches b ON s.batch_id = b.id
        JOIN courses c ON sc.course_id = c.id
        WHERE b.center_code = ?
        ORDER BY b.batch_code, c.course_code
    ''', (center_code,))
    assignments = cursor.fetchall()

    conn.close()
    return render_template('center/assign_course_to_batch.html', batches=batches, courses=courses, message=message, assignments=assignments)



@app.route('/student/my_courses')
def student_my_courses():
    if 'student_id' not in session:
        return redirect('/student_login')

    student_id = session['student_id']
    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''SELECT courses.* FROM courses
                      JOIN student_courses ON courses.id = student_courses.course_id
                      WHERE student_courses.student_id = ?''', (student_id,))
    courses = cursor.fetchall()
    conn.close()
    return render_template('student/my_courses.html', courses=courses)


@app.route('/student/view_course/<int:course_id>')
def student_view_course(course_id):
    if 'student_id' not in session:
        return redirect('/student_login')

    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get course info
    cursor.execute("SELECT * FROM courses WHERE id = ?", (course_id,))
    course = cursor.fetchone()

    if not course:
        return "Course not found", 404

    # Get modules for this course
    cursor.execute("SELECT * FROM modules WHERE course_id = ?", (course_id,))
    modules = cursor.fetchall()

    # Get all lessons for all modules
    lessons = {}
    for module in modules:
        cursor.execute("SELECT * FROM lessons WHERE module_id = ?", (module['id'],))
        module_lessons = cursor.fetchall()
        lessons[module['id']] = module_lessons

    conn.close()

    return render_template("student/view_course.html", course=course, modules=modules, lessons=lessons)









# Student Login
@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    error = None
    if request.method == 'POST':
        student_id = request.form['student_id']
        mobile = request.form['mobile']

        conn = sqlite3.connect('lms.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE student_id = ? AND mobile = ?", (student_id, mobile))
        student = cursor.fetchone()
        conn.close()

        if student:
            session['student_logged_in'] = True  # ✅ THIS LINE ADDED
            session['student_id'] = student['id']   # Use database primary key (id)
            session['student_code'] = student['student_id']
            session['student_name'] = student['name']
            session['center_code'] = student['center_code']
            return redirect('/student_panel')
        else:
            error = "Invalid Student ID or Mobile Number."

    return render_template('student/login.html', error=error)



# Student Panel
@app.route('/student_panel')
def student_panel():
    if not session.get('student_logged_in'):
        return redirect('/student_login')

    student_id = session.get('student_id')  # This is the `id`, primary key
    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT * FROM students WHERE id = ?", (student_id,))
    student = cur.fetchone()

    cur.execute("SELECT * FROM centers WHERE center_code = ?", (student['center_code'],))
    center = cur.fetchone()

    conn.close()

    return render_template('student/student_panel.html', student=student, center=center)




@app.route('/student/profile')
def student_profile():
    if 'student_id' not in session:
        return redirect('/student_login')  # Adjust as needed

    student_id = session['student_id']

    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
    student = cursor.fetchone()

    return render_template('student/student_profile.html', student=student)


import os
from werkzeug.utils import secure_filename

@app.route('/student/edit_profile', methods=['GET', 'POST'])
def edit_student_profile():
    if 'student_id' not in session:
        return redirect('/student_login')

    student_id = session['student_id']
    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if request.method == 'POST':
        form = request.form

        update_query = '''
            UPDATE students SET
                father_name=?, dob=?, gender=?, alt_mobile=?, address=?,
                city=?, pin_code=?, state=?, qualification=?, passing_year=?,
                school=?, board=?, admission_date=?, status=?
            WHERE id=?
        '''
        values = (
            form['father_name'],
            form['dob'],
            form['gender'],
            form['alt_mobile'],
            form['address'],
            form['city'],
            form['pin_code'],
            form['state'],
            form['qualification'],
            form['passing_year'],
            form['school_college'],        # mapped to "school"
            form['board_university'],      # mapped to "board"
            form['admission_date'],
            form.get('status', 'Active'),  # optional status field
            student_id
        )

        cursor.execute(update_query, values)
        conn.commit()
        conn.close()
        return redirect('/student/profile')

    # ✅ GET request - fix this line to use student_id correctly
    cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
    student = cursor.fetchone()
    conn.close()

    return render_template('student/edit_profile.html', student=student)






@app.route('/student_logout')
def student_logout():
    session.clear()
    return redirect('/student_login')












if __name__ == '__main__':
    init_db()
    app.run(debug=True)
