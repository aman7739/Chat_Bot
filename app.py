import os
import csv
import re
import pickle
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Third-party imports
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# 1. LOAD ENVIRONMENT VARIABLES
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "super-secret-key")
CORS(app)

# ----- CONFIGURATION -----
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "620061")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_EMAIL_PASSWORD = os.getenv("ADMIN_EMAIL_PASSWORD")
COLLEGE_PHONE = os.getenv("COLLEGE_PHONE", "919876543210")

# ----- PATHS -----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")
VECTORIZER_PATH = os.path.join(BASE_DIR, "vectorizer.pkl")

# Folders
LOG_DIR = os.path.join(BASE_DIR, "logs")
PDF_DIR = os.path.join(BASE_DIR, "pdfs")
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(PDF_DIR, exist_ok=True)

# Files
LOG_FILE = os.path.join(LOG_DIR, "logs.csv")
FEEDBACK_FILE = os.path.join(LOG_DIR, "feedback.csv")
LEADS_FILE = os.path.join(LOG_DIR, "leads.csv")
APPOINTMENTS_FILE = os.path.join(LOG_DIR, "appointments.csv")

# ----- LOAD AI MODEL -----
try:
    with open(MODEL_PATH, "rb") as f: model = pickle.load(f)
    with open(VECTORIZER_PATH, "rb") as f: vectorizer = pickle.load(f)
    print("[SUCCESS] AI Model Loaded!")
except FileNotFoundError:
    print("[ERROR] Model files not found! Run 'python train_model.py' first.")

# ----- PREPROCESS FUNCTION -----
def preprocess(text):
    text = str(text).lower().strip()
    text = re.sub(r"[^a-z0-9\u0900-\u097F\s]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# ----- RESPONSES (COMPLETE WITH ALL INTENTS) -----
responses_en = {
    "greeting": "Hello! 👋 I'm your college enquiry assistant. How can I help you today? Feel free to ask about admissions, fees, courses, or anything else!",
    
    "thanks": "You're very welcome! 😊 If you have any more questions, feel free to ask. I'm here to help!",
    
    "goodbye": "Goodbye! 👋 Have a great day! Feel free to come back anytime you need help with college information.",
    
    "fees": "💰 **Fee Structure:**\n\n• B.Tech: Rs.1,00,000 per year\n• Diploma: Rs.50,000 per year\n• MCA: Rs.80,000 per year\n\nThis includes tuition and lab fees. Would you like to know about scholarship options?",
    
    "courses": "📚 **Available Courses:**\n\n**B.Tech (4 Years):**\n• Computer Science Engineering (CSE)\n• Information Technology (IT)\n• Mechanical Engineering (ME)\n• Civil Engineering (CE)\n• Electronics & Communication (ECE)\n\n**Diploma (3 Years):**\n• Multiple branches available\n\n**MCA (2 Years):**\n• Master of Computer Applications\n\nAll programs are AICTE approved!",
    
    "timings": "⏰ **College Timings:**\n\n• Monday-Friday: 9:00 AM - 4:00 PM\n• Saturday: 9:00 AM - 1:00 PM\n• Sunday: Holiday\n\n**Office Hours:** 9:00 AM - 5:00 PM (Weekdays)",
    
    "admission": "📝 **Admission Process:**\n\n1. Online/Offline application\n2. Document verification\n3. Entrance exam scores (JEE/State level)\n4. Counselling & seat allocation\n5. Fee payment\n\n**Session 2025-26:** Admissions start in June-July.\n\nWould you like to book a campus visit?",
    
    "hostel": "🏠 **Hostel Facilities:**\n\n• Separate hostels for Boys & Girls\n• AC & Non-AC rooms available\n• 2/3 sharing rooms\n• Mess with quality food\n• 24/7 Security & Warden\n• Wi-Fi, Laundry, Common room\n\n**Hostel Fee:** Rs.60,000/year (including mess)\n\nWould you like more details?",
    
    "transport": "🚌 **Transport Facility:**\n\nCollege bus service available from major locations across Bhopal including:\n• Habibganj, MP Nagar, Arera Colony\n• Kolar, Ayodhya Bypass, Hoshangabad Road\n• BHEL, Bairagarh, and more\n\n**Annual Bus Fee:** Rs.12,000\n**Monthly Pass:** Rs.1,200\n\nBus timings align with college schedule. Safe and comfortable transport!",
    
    "placement": "🎯 **Placement Record:**\n\n• **Highest Package:** 32 LPA\n• **Average Package:** 6 LPA\n• **Placement Rate:** 85%+\n\n**Top Recruiters:** TCS, Infosys, Wipro, Tech Mahindra, Cognizant, Capgemini, L&T, Amazon, Microsoft, and 50+ companies\n\n**Training Provided:** Aptitude, Technical, Soft skills, Mock interviews",
    
    "scholarship": "🎓 **Scholarship Opportunities:**\n\n• **Merit-based:** 85%+ in 12th → 25% fee waiver\n• **SC/ST:** As per Govt. norms\n• **OBC/EWS:** As per Govt. schemes\n• **Girl Students:** Special concessions\n• **Sports Quota:** Available\n\nScholarships are processed after admission. Documents required at the time of verification.",
    
    "exams": "📋 **Examination Pattern:**\n\n• **Internal Assessment:** 30 marks (20% attendance mandatory)\n• **End Semester Exam:** 70 marks\n• **Mid-term Tests:** Unit tests conducted\n• **Practical Exams:** Separate for lab subjects\n\n**Exam Schedule:** Released 15 days before exams on the college portal.\n\nRegular assessments, assignments, and viva included.",
    
    "contact": f"📞 **Contact Information:**\n\n• **Phone:** +{COLLEGE_PHONE}\n• **Email:** {ADMIN_EMAIL}\n• **Address:** Anand Nagar, Bhopal, M.P.\n• **Timing:** Mon-Fri 9 AM - 5 PM\n\nYou can also WhatsApp us or visit the campus directly!",
    
    "location": "📍 **College Location:**\n\n**Address:** Anand Nagar, Bhopal, Madhya Pradesh\n\n• Easily accessible by public transport\n• Near major landmarks in Bhopal\n• Well-connected by road\n• 20 acres green campus\n\n**How to Reach:** Bus service available from Habibganj, MP Nagar, and other major areas. Would you like the Google Maps link?",
    
    "faculty": "👨‍🏫 **Faculty Details:**\n\n• **100+ Experienced Faculty Members**\n• Most hold PhD & M.Tech degrees\n• Industry experience of 5-20 years\n• Research publications in reputed journals\n• Student-Teacher ratio: 15:1\n• Regular workshops & training for faculty\n\nDepartment-wise experienced HODs and professors guide students throughout their academic journey.",
    
    "result": "📊 **Result Information:**\n\n• Results are published on the college portal\n• Usually declared within 30 days of exam\n• Semester-wise grading system\n• Marksheets available for download\n• SGPA & CGPA calculated\n\n**To Check Result:**\n1. Visit college website\n2. Go to Student Portal\n3. Enter Roll Number & DOB\n4. Download marksheet\n\nFor any discrepancies, contact the examination cell.",
    
    "documents": "📄 **Documents Required for Admission:**\n\n**Mandatory:**\n• 10th Marksheet & Certificate\n• 12th Marksheet & Certificate\n• Transfer Certificate (TC)\n• Migration Certificate\n• Character Certificate\n• Aadhar Card\n• 4 Passport size photos\n\n**For Reserved Categories:**\n• Caste Certificate (SC/ST/OBC)\n• Income Certificate (EWS)\n• Domicile Certificate\n\n**Original + 2 photocopies** of each document required.",
    
    "library": "📚 **Library Facilities:**\n\n• 50,000+ Books collection\n• National & International Journals\n• Digital Library with e-resources\n• Reading room with 200+ seating\n• Internet facility\n• Question paper bank\n\n**Timing:** 8:00 AM - 8:00 PM (All working days)\n\nStudent can issue 3 books for 15 days. Separate reference section available.",
    
    "facilities": "🏫 **Campus Facilities:**\n\n• Modern Computer Labs (500+ systems)\n• Well-equipped Workshops\n• Auditorium (500 seating)\n• Sports Complex\n• Cafeteria & Food Court\n• Medical Room\n• ATM & Banking\n• Parking Area\n• 24/7 Security with CCTV\n• Full Wi-Fi Campus\n• Separate Common rooms\n\n20-acre green campus with modern infrastructure!",
    
    "infrastructure": "🏗️ **Infrastructure:**\n\n• Modern Academic Blocks\n• Separate Department Buildings\n• Air-conditioned Classrooms\n• Smart Classrooms with projectors\n• Seminar Halls\n• Conference Rooms\n• Well-maintained Labs\n• Green campus with landscaping\n• Rainwater harvesting\n• Solar panels\n\n**Total Area:** 20 acres\nAll facilities as per AICTE norms.",
    
    "eligibility": "✅ **Eligibility Criteria:**\n\n**For B.Tech:**\n• 12th Pass with PCM (Physics, Chemistry, Maths)\n• Minimum 60% aggregate (50% for SC/ST)\n• Valid JEE Main / State entrance score\n\n**For Diploma:**\n• 10th Pass with 50%+ marks\n• Mathematics & Science mandatory\n\n**For MCA:**\n• Graduation with 50%+ (BCA/B.Sc IT preferred)\n• Valid entrance exam score\n\nAge limit as per AICTE norms.",
    
    "duration": "⏳ **Course Duration:**\n\n• **B.Tech:** 4 Years (8 Semesters)\n• **Diploma:** 3 Years (6 Semesters)\n• **MCA:** 2 Years (4 Semesters)\n\n**Semester System:** Each semester is 6 months with theory, practical, and project work.\n\n**Academic Year:** July to June\n**Vacations:** Summer (May-June), Winter (Dec-Jan)",
    
    "labs": "🔬 **Laboratory Facilities:**\n\n**Computer Labs:**\n• 500+ high-speed computers\n• Latest software & tools\n• Separate labs for different subjects\n\n**Engineering Labs:**\n• Electronics Lab\n• Mechanical Workshop\n• Civil Engineering Lab\n• CAD/CAM Lab\n• Project Development Center\n\nAll labs are equipped with modern equipment and supervised by experienced lab assistants.",
    
    "sports": "⚽ **Sports Facilities:**\n\n**Outdoor:**\n• Cricket Ground\n• Football Field\n• Basketball Court\n• Volleyball Court\n• Badminton Court\n• Athletic Track\n\n**Indoor:**\n• Table Tennis\n• Chess\n• Carrom\n• Gymnasium with modern equipment\n\n**Annual Sports Meet** organized every year. Students can participate in inter-college tournaments.",
    
    "events": "🎉 **College Events:**\n\n**Annual Events:**\n• Tech Fest (Technical competitions)\n• Cultural Fest (Dance, Music, Drama)\n• Sports Meet\n• Freshers Party\n• Farewell Party\n\n**Regular Activities:**\n• Technical Workshops\n• Guest Lectures\n• Industry Visits\n• Seminars & Webinars\n• Coding Competitions\n• Hackathons\n\nActive clubs: Technical, Cultural, Sports, Literary. Students are encouraged to participate!"
}

responses_hi = {
    "greeting": "Namaste! 🙏 Main aapki college enquiry assistant hoon. Main aapki kaise madad kar sakti hoon? Admission, fees, courses ke baare mein pooch sakte hain!",
    
    "thanks": "Aapka swagat hai! 😊 Agar aur koi sawal ho toh zaroor puchiye. Main yahan madad ke liye hoon!",
    
    "goodbye": "Alvida! 👋 Aapka din shubh ho! Jab bhi zaroorat ho, wapas aa sakte hain!",
    
    "fees": "💰 **Fees Ki Jankari:**\n\n• B.Tech: Rs.1,00,000 saalana\n• Diploma: Rs.50,000 saalana\n• MCA: Rs.80,000 saalana\n\nIsmein tuition aur lab fees shamil hai. Scholarship ke baare mein jaanna chahenge?",
    
    "courses": "📚 **Uplabdh Courses:**\n\n**B.Tech (4 Saal):**\n• Computer Science Engineering (CSE)\n• Information Technology (IT)\n• Mechanical Engineering (ME)\n• Civil Engineering (CE)\n• Electronics & Communication (ECE)\n\n**Diploma (3 Saal):**\n• Kai branches uplabdh hain\n\n**MCA (2 Saal):**\n• Master of Computer Applications\n\nSabhi courses AICTE approved hain!",
    
    "timings": "⏰ **College Ka Samay:**\n\n• Somwar-Shukrawar: 9:00 AM - 4:00 PM\n• Shaniwar: 9:00 AM - 1:00 PM\n• Raviwar: Chutti\n\n**Office Ka Samay:** 9:00 AM - 5:00 PM (Hafta bhar)",
    
    "admission": "📝 **Admission Process:**\n\n1. Online/Offline application bharein\n2. Documents verification\n3. Entrance exam scores (JEE/State level)\n4. Counselling aur seat allocation\n5. Fees payment karein\n\n**Session 2025-26:** Admission June-July mein shuru honge.\n\nCampus visit book karna chahenge?",
    
    "hostel": "🏠 **Hostel Suvidha:**\n\n• Ladke aur ladkiyon ke liye alag hostel\n• AC aur Non-AC rooms uplabdh\n• 2/3 logo ka sharing\n• Quality food ke saath mess\n• 24/7 Security aur Warden\n• Wi-Fi, Laundry, Common room\n\n**Hostel Fees:** Rs.60,000/saal (mess shamil)\n\nAur jankari chahiye?",
    
    "transport": "🚌 **Transport Suvidha:**\n\nBhopal ke pramukh sthanon se college bus service uplabdh hai:\n• Habibganj, MP Nagar, Arera Colony\n• Kolar, Ayodhya Bypass, Hoshangabad Road\n• BHEL, Bairagarh aur bhi bahut jagah se\n\n**Saalana Bus Fees:** Rs.12,000\n**Monthly Pass:** Rs.1,200\n\nBus ka samay college ke schedule ke anusaar hai. Surakshit aur aaraamdayak!",
    
    "placement": "🎯 **Placement Record:**\n\n• **Highest Package:** 32 LPA\n• **Average Package:** 6 LPA\n• **Placement Rate:** 85%+\n\n**Top Companies:** TCS, Infosys, Wipro, Tech Mahindra, Cognizant, Capgemini, L&T, Amazon, Microsoft aur 50+ companies\n\n**Training:** Aptitude, Technical, Soft skills, Mock interviews di jati hai",
    
    "scholarship": "🎓 **Scholarship Suvidha:**\n\n• **Merit basis:** 85%+ in 12th → 25% fees mein kami\n• **SC/ST:** Sarkar ke niyam anusar\n• **OBC/EWS:** Sarkar ki schemes\n• **Girl Students:** Vishesh chhoot\n• **Sports Quota:** Uplabdh\n\nScholarship admission ke baad process hoti hai. Documents verification ke samay chahiye.",
    
    "exams": "📋 **Pariksha Pattern:**\n\n• **Internal Assessment:** 30 marks (20% attendance zaruri)\n• **End Semester Exam:** 70 marks\n• **Mid-term Tests:** Unit tests liye jaate hain\n• **Practical Exams:** Lab subjects ke liye alag\n\n**Exam Schedule:** Pariksha se 15 din pehle college portal par aata hai.\n\nRegular assessments, assignments aur viva shamil hain.",
    
    "contact": f"📞 **Sampark Jankari:**\n\n• **Phone:** +{COLLEGE_PHONE}\n• **Email:** {ADMIN_EMAIL}\n• **Pata:** Anand Nagar, Bhopal, M.P.\n• **Samay:** Somwar-Shukrawar 9 AM - 5 PM\n\nAap WhatsApp bhi kar sakte hain ya seedha campus visit karein!",
    
    "location": "📍 **College Ki Sthiti:**\n\n**Pata:** Anand Nagar, Bhopal, Madhya Pradesh\n\n• Public transport se aasani se pahuncha ja sakta hai\n• Bhopal ke pramukh sthanon ke paas\n• Sadak se acchi tarah juda hua\n• 20 acre hara-bhara campus\n\n**Kaise Pahunche:** Habibganj, MP Nagar aur anya pramukh areas se bus service uplabdh hai. Google Maps link chahiye?",
    
    "faculty": "👨‍🏫 **Shikshak Jankari:**\n\n• **100+ Anubhavi Shikshak**\n• Adhiktar ke paas PhD aur M.Tech degree hai\n• 5-20 saal ka industry experience\n• Prasiddh journals mein research publication\n• Student-Teacher ratio: 15:1\n• Regular workshops aur training\n\nHar department mein anubhavi HOD aur professors students ki madad karte hain.",
    
    "result": "📊 **Result Jankari:**\n\n• Result college portal par publish hote hain\n• Aamtaur par exam ke 30 din baad aate hain\n• Semester wise grading system\n• Marksheet download kar sakte hain\n• SGPA aur CGPA calculate hota hai\n\n**Result Dekhne Ke Liye:**\n1. College website par jaye\n2. Student Portal mein jaye\n3. Roll Number aur DOB enter karein\n4. Marksheet download karein\n\nKisi bhi samasya ke liye examination cell se sampark karein.",
    
    "documents": "📄 **Admission Ke Liye Zaruri Documents:**\n\n**Avashyak:**\n• 10th Marksheet aur Certificate\n• 12th Marksheet aur Certificate\n• Transfer Certificate (TC)\n• Migration Certificate\n• Character Certificate\n• Aadhar Card\n• 4 Passport size photos\n\n**Aarakshit Category Ke Liye:**\n• Caste Certificate (SC/ST/OBC)\n• Income Certificate (EWS)\n• Domicile Certificate\n\n**Original + 2 photocopies** har document ki zaruri hai.",
    
    "library": "📚 **Library Suvidha:**\n\n• 50,000+ Books\n• National aur International Journals\n• Digital Library with e-resources\n• Reading room 200+ seating ke saath\n• Internet suvidha\n• Question paper bank\n\n**Samay:** 8:00 AM - 8:00 PM (Sabhi working days)\n\nStudent 3 books 15 din ke liye le sakta hai. Reference section alag hai.",
    
    "facilities": "🏫 **Campus Suvidhayen:**\n\n• Modern Computer Labs (500+ systems)\n• Acche Workshops\n• Auditorium (500 seating)\n• Sports Complex\n• Cafeteria aur Food Court\n• Medical Room\n• ATM aur Banking\n• Parking Area\n• 24/7 Security with CCTV\n• Poora Wi-Fi Campus\n• Alag Common rooms\n\n20-acre hara campus modern infrastructure ke saath!",
    
    "infrastructure": "🏗️ **Infrastructure:**\n\n• Modern Academic Buildings\n• Har Department ki alag Building\n• AC Classrooms\n• Smart Classrooms projectors ke saath\n• Seminar Halls\n• Conference Rooms\n• Acchi Labs\n• Hara campus landscaping ke saath\n• Rainwater harvesting\n• Solar panels\n\n**Kul Area:** 20 acre\nSabhi suvidhayen AICTE norms ke anusaar.",
    
    "eligibility": "✅ **Yogyata (Eligibility):**\n\n**B.Tech Ke Liye:**\n• 12th Pass PCM ke saath\n• Minimum 60% marks (50% for SC/ST)\n• Valid JEE Main / State entrance score\n\n**Diploma Ke Liye:**\n• 10th Pass 50%+ marks ke saath\n• Maths aur Science zaruri\n\n**MCA Ke Liye:**\n• Graduation 50%+ ke saath (BCA/B.Sc IT best)\n• Valid entrance exam score\n\nAge limit AICTE norms ke anusaar.",
    
    "duration": "⏳ **Course Ki Avadhi:**\n\n• **B.Tech:** 4 Saal (8 Semester)\n• **Diploma:** 3 Saal (6 Semester)\n• **MCA:** 2 Saal (4 Semester)\n\n**Semester System:** Har semester 6 mahine ka theory, practical aur project work ke saath.\n\n**Academic Year:** July se June\n**Chhutti:** Summer (May-June), Winter (Dec-Jan)",
    
    "labs": "🔬 **Laboratory Suvidhayen:**\n\n**Computer Labs:**\n• 500+ tez computers\n• Latest software aur tools\n• Alag-alag subjects ke liye labs\n\n**Engineering Labs:**\n• Electronics Lab\n• Mechanical Workshop\n• Civil Engineering Lab\n• CAD/CAM Lab\n• Project Development Center\n\nSabhi labs modern equipment se equipped hain aur anubhavi lab assistants dwara supervised.",
    
    "sports": "⚽ **Khel-kood Suvidhayen:**\n\n**Bahar:**\n• Cricket Ground\n• Football Field\n• Basketball Court\n• Volleyball Court\n• Badminton Court\n• Athletic Track\n\n**Andar:**\n• Table Tennis\n• Chess\n• Carrom\n• Gymnasium modern equipment ke saath\n\n**Annual Sports Meet** har saal organize hota hai. Students inter-college tournaments mein bhi participate kar sakte hain.",
    
    "events": "🎉 **College Events:**\n\n**Saalana Events:**\n• Tech Fest (Technical competitions)\n• Cultural Fest (Dance, Music, Drama)\n• Sports Meet\n• Freshers Party\n• Farewell Party\n\n**Regular Activities:**\n• Technical Workshops\n• Guest Lectures\n• Industry Visits\n• Seminars & Webinars\n• Coding Competitions\n• Hackathons\n\nActive clubs: Technical, Cultural, Sports, Literary. Students ko participate karne ke liye encourage kiya jata hai!"
}

# ----- EMAIL HELPER -----
def send_email_notification(subject, body):
    if not ADMIN_EMAIL or not ADMIN_EMAIL_PASSWORD:
        print("[WARNING] Email not configured in .env")
        return False
    try:
        msg = MIMEMultipart()
        msg['From'] = ADMIN_EMAIL
        msg['To'] = ADMIN_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(ADMIN_EMAIL, ADMIN_EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"[ERROR] Email failed: {e}")
        return False

# ----- HTML ROUTES -----

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

# ----- API ROUTES (GET DATA) -----

@app.route("/api/logs")
def get_logs():
    if request.args.get("password") != ADMIN_PASSWORD:
        return jsonify({"error": "Unauthorized"}), 403
    data = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            data = list(csv.reader(f))
    return jsonify(data)

@app.route("/api/leads")
def get_leads():
    if request.args.get("password") != ADMIN_PASSWORD:
        return jsonify({"error": "Unauthorized"}), 403
    data = []
    if os.path.exists(LEADS_FILE):
        with open(LEADS_FILE, "r", encoding="utf-8") as f:
            data = list(csv.reader(f))
    return jsonify(data)

@app.route("/api/appointments")
def get_appointments():
    if request.args.get("password") != ADMIN_PASSWORD:
        return jsonify({"error": "Unauthorized"}), 403
    data = []
    if os.path.exists(APPOINTMENTS_FILE):
        with open(APPOINTMENTS_FILE, "r", encoding="utf-8") as f:
            data = list(csv.reader(f))
    return jsonify(data)

@app.route("/api/feedback")
def get_feedback():
    if request.args.get("password") != ADMIN_PASSWORD:
        return jsonify({"error": "Unauthorized"}), 403
    data = []
    if os.path.exists(FEEDBACK_FILE):
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
            data = list(csv.reader(f))
    return jsonify(data)

# ----- ACTION ROUTES (POST DATA) -----

@app.route("/submit-lead", methods=["POST"])
def submit_lead():
    data = request.json
    name, phone, course = data.get("name"), data.get("phone"), data.get("course")
    
    if not all([name, phone, course]):
        return jsonify({"status": "error", "message": "Missing fields"}), 400

    try:
        if not os.path.exists(LEADS_FILE):
            with open(LEADS_FILE, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(["timestamp", "name", "phone", "course"])
        
        with open(LEADS_FILE, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([datetime.now(), name, phone, course])
        
        send_email_notification(f"New Lead: {name}", f"Name: {name}\nPhone: {phone}\nCourse: {course}")
        return jsonify({"status": "success"})
    except Exception as e:
        print(e)
        return jsonify({"status": "error"}), 500

@app.route("/book-appointment", methods=["POST"])
def book_appointment():
    data = request.json
    name, phone, date, time = data.get("name"), data.get("phone"), data.get("date"), data.get("time")

    try:
        if not os.path.exists(APPOINTMENTS_FILE):
             with open(APPOINTMENTS_FILE, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(["timestamp", "name", "phone", "date", "time"])
        
        with open(APPOINTMENTS_FILE, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([datetime.now(), name, phone, date, time])
        
        send_email_notification(f"New Appointment: {name}", f"Name: {name}\nDate: {date}\nTime: {time}")
        return jsonify({"status": "success"})
    except:
        return jsonify({"status": "error"}), 500

@app.route("/feedback", methods=["POST"])
def save_feedback():
    d = request.json
    try:
        if not os.path.exists(FEEDBACK_FILE):
             with open(FEEDBACK_FILE, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(["timestamp", "user_message", "bot_answer", "feedback"])
        with open(FEEDBACK_FILE, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([datetime.now(), d.get("message"), d.get("answer"), d.get("feedback")])
        return jsonify({"status": "success"})
    except: 
        return jsonify({"status": "error"}), 500

# ----- PDF DOWNLOAD -----
@app.route("/download/<pdf_type>")
def download_pdf(pdf_type):
    pdf_map = {
        "brochure": "admission_brochure.pdf",
        "fees": "fee_structure.pdf",
        "transport": "transport_routes.pdf"
    }
    filename = pdf_map.get(pdf_type)
    if filename:
        return send_from_directory(PDF_DIR, filename, as_attachment=True)
    return jsonify({"error": "File not found"}), 404

# ----- CHAT LOGIC (AI BRAIN) -----
@app.route("/chat", methods=["POST"])
def chat():
    raw_message = request.json.get("message", "")
    language = request.json.get("language", "en")
    responses = responses_hi if language == "hi" else responses_en
    
    clean_message = preprocess(raw_message)
    predicted = None
    max_prob = 0.0
    is_fallback = False

    # 1. ENHANCED KEYWORD SHORTCUTS
    keyword_intents = {
        # Greeting
        "hello": "greeting", "hi": "greeting", "hey": "greeting", "hlo": "greeting", "hii": "greeting",
        "namaste": "greeting", "namaskar": "greeting", "pranam": "greeting",
        
        # Thanks
        "thanks": "thanks", "thank": "thanks", "thanku": "thanks", "dhanyavaad": "thanks", "shukriya": "thanks",
        
        # Goodbye
        "bye": "goodbye", "goodbye": "goodbye", "alvida": "goodbye", "tata": "goodbye",
        
        # Fees
        "fee": "fees", "fees": "fees", "money": "fees", "cost": "fees", "price": "fees", 
        "kitna": "fees", "paisa": "fees", "kharcha": "fees",
        
        # Courses
        "course": "courses", "courses": "courses", "branch": "courses", "stream": "courses",
        "konse": "courses", "kya": "courses",
        
        # Timings
        "timing": "timings", "time": "timings", "timings": "timings", "schedule": "timings",
        "kab": "timings", "samay": "timings",
        
        # Admission
        "admission": "admission", "apply": "admission", "enroll": "admission", "pravesh": "admission",
        
        # Hostel
        "hostel": "hostel", "accommodation": "hostel", "residence": "hostel", "pg": "hostel",
        
        # Transport
        "transport": "transport", "bus": "transport",
        
        # Placement
        "placement": "placement", "job": "placement", "package": "placement", "naukri": "placement",
        
        # Scholarship
        "scholarship": "scholarship", "financial": "scholarship", "concession": "scholarship",
        
        # Exams
        "exam": "exams", "exams": "exams", "test": "exams", "pareeksha": "exams",
        
        # Contact
        "contact": "contact", "phone": "contact", "email": "contact", "call": "contact",
        "number": "contact",
        
        # Location
        "location": "location", "address": "location", "where": "location", "city": "location", 
        "place": "location", "pata": "location", "kahan": "location",
        
        # Faculty
        "faculty": "faculty", "teacher": "faculty", "professor": "faculty", "shikshak": "faculty",
        
        # Result
        "result": "result", "marks": "result", "marksheet": "result",
        
        # Documents
        "document": "documents", "documents": "documents", "kagaz": "documents",
        
        # Library
        "library": "library", "books": "library",
        
        # Facilities
        "facility": "facilities", "facilities": "facilities", "suvidha": "facilities",
        
        # Infrastructure
        "infrastructure": "infrastructure", "campus": "infrastructure", "building": "infrastructure",
        
        # Eligibility
        "eligibility": "eligibility", "eligible": "eligibility", "criteria": "eligibility",
        "yogyata": "eligibility",
        
        # Duration
        "duration": "duration", "years": "duration", "period": "duration", "avadhi": "duration",
        
        # Labs
        "lab": "labs", "labs": "labs", "laboratory": "labs", "workshop": "labs",
        
        # Sports
        "sports": "sports", "games": "sports", "gym": "sports", "khel": "sports",
        
        # Events
        "events": "events", "fest": "events", "function": "events"
    }
    
    if clean_message in keyword_intents:
        predicted = keyword_intents[clean_message]
        max_prob = 1.0

    # 2. AI PREDICTION
    if not predicted:
        try:
            X_test = vectorizer.transform([clean_message])
            probs = model.predict_proba(X_test)[0]
            max_prob = float(probs.max())
            predicted = model.classes_[probs.argmax()]
        except Exception as e:
            print(f"[ERROR] Prediction failed: {e}")
            is_fallback = True

    # 3. CONFIDENCE CHECK
    if max_prob < 0.25:
        is_fallback = True
        answer = "I'm not fully sure about that. Could you please rephrase your question? Or contact our office for accurate information." if language == "en" else "Mujhe iske baare mein poori jankari nahi hai. Kya aap apna sawal dusre tarike se pooch sakte hain? Ya office se sampark karein."
    else:
        answer = responses.get(predicted)
        if not answer:
            answer = "Sorry, I don't have information about that yet. Please contact our office." if language == "en" else "Maaf karein, mere paas abhi iske baare mein jankari nahi hai. Kripya office se sampark karein."
            is_fallback = True
        else:
            is_fallback = False

    # 4. LOGGING
    try:
        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(["timestamp", "user_message", "predicted_intent", "confidence", "status", "language"])
        
        with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                raw_message,
                predicted if predicted else "unknown",
                f"{round(max_prob * 100, 0)}%",
                "fallback" if is_fallback else "normal",
                language
            ])
    except Exception as e:
        print(f"[ERROR] Logging failed: {e}")

    # 5. SMART PDF SUGGESTIONS
    pdf_suggestions = []
    if predicted in ["fees", "cost"]: 
        pdf_suggestions.append("fees")
    if predicted in ["admission", "apply"]: 
        pdf_suggestions.append("brochure")
    if predicted in ["transport", "bus"]: 
        pdf_suggestions.append("transport")

    return jsonify({
        "answer": answer,
        "fallback": is_fallback,
        "pdf_suggestions": pdf_suggestions,
        "intent": predicted,
        "confidence": round(max_prob * 100, 2)
    })

if __name__ == "__main__":
    # Initialize log files with headers if they don't exist
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["timestamp", "user_message", "predicted_intent", "confidence", "status", "language"])
    
    if not os.path.exists(LEADS_FILE):
        with open(LEADS_FILE, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["timestamp", "name", "phone", "course"])
    
    if not os.path.exists(FEEDBACK_FILE):
        with open(FEEDBACK_FILE, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["timestamp", "user_message", "bot_answer", "feedback"])
    
    if not os.path.exists(APPOINTMENTS_FILE):
        with open(APPOINTMENTS_FILE, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["timestamp", "name", "phone", "date", "time"])
    
    print("\n" + "="*60)
    print("COLLEGE ENQUIRY CHATBOT - READY!")
    print("="*60)
    print(f"[OK] AI Model Loaded Successfully")
    print(f"[OK] College Location: Anand Nagar, Bhopal, M.P.")
    print(f"[OK] Supported Intents: 20+")
    print(f"[OK] Email Notifications: {'Enabled' if ADMIN_EMAIL else 'Disabled'}")
    print(f"[OK] Languages: English & Hindi")
    print("="*60)
    print(f"[SERVER] http://127.0.0.1:5000")
    print(f"[DASHBOARD] http://127.0.0.1:5000/dashboard")
    print("="*60 + "\n")
    
    app.run(debug=True, use_reloader=False)