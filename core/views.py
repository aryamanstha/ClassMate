from django.shortcuts import render, get_object_or_404
from .models import (
    Student, Instructor, Course, Section, Textbook,
    BookProvider, CourseTextbook, SectionTextbook,
    Enrollment, Borrow, StudentAccount, InstructorAccount
)
import requests
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth import logout as auth_logout
import json
import sqlite3
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.views.decorators.http import require_POST
import re


DB_PATH = settings.BASE_DIR / "database" / "classmate"

def call_ollama(prompt):
    url = "http://localhost:11434/api/generate"
    response = requests.post(url, json={
        "model": "qwen2.5:1.5b",
        "prompt": prompt,
        "stream": False
    })
    return response.json().get("response", "").strip()


@csrf_exempt
@require_POST
def chatbot_respond(request):
    import json
    from django.http import JsonResponse
    from core.models import (
        Student, Course, Instructor, Section, Textbook,
        SectionTextbook, Enrollment, Borrow
    )

    data = json.loads(request.body)
    user_message = data.get("message", "").strip()

    # Identify logged-in student
    user = request.user
    student = getattr(getattr(user, "studentaccount", None), "student", None)
    sid = student.student_id if student else ""

    if not sid:
        return JsonResponse({"reply": "This assistant is available only to students."})

    intent_prompt = f"""
Classify the student's message into one intent and extract entities.
Return ONLY raw JSON. No markdown. No backticks. No explanations.

The user is a STUDENT with student_id="{sid}".

Output format:
{{
  "intents": [
    {{"name": "get_my_courses", "score": 0.0}},
    {{"name": "get_my_instructors", "score": 0.0}},
    {{"name": "get_my_textbooks", "score": 0.0}},
    {{"name": "get_borrowed_books", "score": 0.0}},
    {{"name": "get_borrow_history", "score": 0.0}},
    {{"name": "get_borrow_status", "score": 0.0}},

    {{"name": "get_course_details", "score": 0.0}},
    {{"name": "get_textbook_details", "score": 0.0}},
    {{"name": "get_required_vs_optional", "score": 0.0}},

    {{"name": "get_my_sections", "score": 0.0}},
    {{"name": "get_section_schedule", "score": 0.0}},

    {{"name": "get_provider_details", "score": 0.0}},
    {{"name": "find_cheaper_textbooks", "score": 0.0}},

    {{"name": "smart_suggestion", "score": 0.0}},

    {{"name": "greeting", "score": 0.0}},
    {{"name": "goodbye", "score": 0.0}},
    {{"name": "unknown", "score": 0.0}}
  ],
  "entities": {{
      "course_id": "",
      "course_name": "",
      "section_id": "",
      "textbook_id": "",
      "textbook_title": "",
      "instructor_name": "",
      "provider_id": "",
      "provider_name": "",
      "borrow_id": ""
  }}
}}
Assign a higher score to the intent that best matches the user's message.
Only ONE intent should have the highest score. All other intents must have lower scores.
The system will select the intent with the highest score, so score assignment must be meaningful.

Rules:
- If message asks about student's courses → intent="get_my_courses".
- If message asks about instructors → intent="get_my_instructors".
- If message asks about sections → intent="get_my_sections".
- If message asks about borrow history or past borrows → intent="get_borrow_history".
- If message asks about due date or status of borrowed book → intent="get_borrow_status".
- If message asks about required vs optional textbooks → intent="get_required_vs_optional".
- If message asks about provider details or contact info → intent="get_provider_details".
- If message asks for cheaper options or cheaper alternatives → intent="find_cheaper_textbooks".
- If message contains a course name or ID or asks about instructor associated with course → intent="get_course_details".
- If message contains a textbook name or ID → intent="get_textbook_details".
- If message asks for summaries, alternatives, study tips, or recommendations → intent="smart_suggestion".
- If unclear, set highest score to "unknown".

User message: "{user_message}"
"""

    raw = call_ollama(intent_prompt)
    print("RAW CLASSIFIER:", raw)

    cleaned = raw.replace("```json", "").replace("```", "").replace("`", "").strip()

    try:
        intent_data = json.loads(cleaned)
    except:
        return JsonResponse({"reply": "I couldn't classify your request."})

    intents = intent_data.get("intents", [])
    entities = intent_data.get("entities", {})

    # Evaluate highest scoring intent
    intents_sorted = sorted(intents, key=lambda x: x["score"], reverse=True)
    top_intent = intents_sorted[0]["name"] if intents_sorted else "unknown"

    # ------------------------------------------------------------------
    # STEP 2 — ORM HANDLERS (STUDENT ONLY)
    # ------------------------------------------------------------------

    results = []

    # 1. Student's Courses
    if top_intent == "get_my_courses":
        enrollments = Enrollment.objects.filter(student__student_id=sid)
        for enr in enrollments:
            c = enr.section.course
            results.append({
                "course_id": c.course_id,
                "course_name": c.course_name,
                "description": c.description,
                "section_id": enr.section.section_id
            })

    # # 2. Borrowed Books
    # elif top_intent == "get_borrowed_books":
    #     borrows = Borrow.objects.filter(student__student_id=sid)
    #     for b in borrows:
    #         results.append({
    #             "title": b.textbook.title,
    #             "status": b.status,
    #             "borrowed_from": str(b.start_date),
    #             "due_date": str(b.end_date)
    #         })

   
    elif top_intent == "get_my_textbooks":
        enrollments = Enrollment.objects.filter(student__student_id=sid)
        for enr in enrollments:
            sec = enr.section
            stbooks = SectionTextbook.objects.filter(section=sec)
            for st in stbooks:
                results.append({
                    "course_name": sec.course.course_name,
                    "textbook_title": st.textbook.title,
                    "requirement": st.requirement_type
                })

    #  Student Sections
    elif top_intent == "get_my_sections":
        enrollments = Enrollment.objects.filter(student__student_id=sid)
        for enr in enrollments:
            sec = enr.section
            results.append({
                "section_id": sec.section_id,
                "course_id": sec.course.course_id,
                "course_name": sec.course.course_name,
                "semester": sec.semester,
                "year": sec.year,
                "instructor": sec.instructor.name
            })

    # Student Instructors
    elif top_intent == "get_my_instructors":
        enrollments = Enrollment.objects.filter(student__student_id=sid)
        seen = {}

        for e in enrollments:
            inst = e.section.instructor
            course = e.section.course

            if inst.instructor_id not in seen:
                seen[inst.instructor_id] = {
                    "instructor_id": inst.instructor_id,
                    "instructor_name": inst.name,
                    "email": inst.email,
                    "phone": inst.phone,
                    "department": inst.department,
                    "courses_taught": set()  
                }

           
            seen[inst.instructor_id]["courses_taught"].add(course.course_name)

        
        for data in seen.values():
            data["courses_taught"] = list(data["courses_taught"])
            results.append(data)

    # Course Details
    elif top_intent == "get_course_details":
        cid = entities.get("course_id", "")
        cname = entities.get("course_name", "")

        if cid:
            course = Course.objects.filter(course_id__iexact=cid).first()
        else:
            course = Course.objects.filter(course_name__icontains=cname).first()

        if course:
            results.append({
                "course_id": course.course_id,
                "course_name": course.course_name,
                "description": course.description
            })
            for sec in Section.objects.filter(course=course).select_related("instructor"):
                results.append({
                    "section_id": sec.section_id,
                    "instructor_id": sec.instructor.instructor_id,
                    "instructor_name": sec.instructor.name,
                    "email": sec.instructor.email,
                    "phone": sec.instructor.phone,
                    "department": sec.instructor.department,
                })
    # Textbook Details
    elif top_intent == "get_textbook_details":
        tid = entities.get("textbook_id", "")
        tname = entities.get("textbook_title", "")

        if tid:
            tb = Textbook.objects.filter(textbook_id__iexact=tid).first()
        else:
            tb = Textbook.objects.filter(title__icontains=tname).first()

        if tb:
            results.append({
                "textbook_id": tb.textbook_id,
                "title": tb.title,
                "edition": tb.edition,
                "author": tb.author,
                "provider": tb.provider.provider_name,
                "price": str(tb.price)
            })

    # Borrow History
    elif top_intent == "get_borrow_history":
        borrows = Borrow.objects.filter(student__student_id=sid).order_by("-start_date")
        if borrows:
            for b in borrows:
                results.append({
                    "textbook_title": b.textbook.title,
                    "author": b.textbook.author,
                    "borrowed_date": str(b.start_date),
                    "returned_date": str(b.end_date) if b.end_date else "Not returned",
                    "status": b.status,
                    "provider": b.textbook.provider.provider_name
                })
        else:
            results.append({"info": "No borrow history found."})

  
    elif top_intent == "get_borrow_status":
        borrows = Borrow.objects.filter(student__student_id=sid, status__icontains="active")
        if borrows:
            for b in borrows:
                results.append({
                    "textbook_title": b.textbook.title,
                    "status": b.status,
                    "borrowed_date": str(b.start_date),
                    "due_date": str(b.end_date) if b.end_date else "No due date set",
                    "days_remaining": (b.end_date - __import__('datetime').date.today()).days if b.end_date else "N/A"
                })
        else:
            results.append({"info": "You have no active borrowed books."})

    #  Required vs Optional Textbooks
    elif top_intent == "get_required_vs_optional":
        enrollments = Enrollment.objects.filter(student__student_id=sid)
        required = []
        optional = []
        
        for enr in enrollments:
            sec = enr.section
            stbooks = SectionTextbook.objects.filter(section=sec)
            for st in stbooks:
                book_info = {
                    "course": sec.course.course_name,
                    "textbook": st.textbook.title,
                    "author": st.textbook.author,
                    "price": str(st.textbook.price),
                    "provider": st.textbook.provider.provider_name
                }
                if "required" in st.requirement_type.lower():
                    required.append(book_info)
                else:
                    optional.append(book_info)
        
        if required:
            results.append({"required_textbooks": required})
        if optional:
            results.append({"optional_textbooks": optional})
        if not required and not optional:
            results.append({"info": "No textbooks assigned to your sections."})

    # Provider Details
    elif top_intent == "get_provider_details":
        pid = entities.get("provider_id", "")
        pname = entities.get("provider_name", "")
        
        if pid:
            provider = BookProvider.objects.filter(provider_id__iexact=pid).first()
        else:
            provider = BookProvider.objects.filter(provider_name__icontains=pname).first()
        
        if provider:
            textbooks = Textbook.objects.filter(provider=provider)
            results.append({
                "provider_id": provider.provider_id,
                "provider_name": provider.provider_name,
                "contact": provider.contact_number,
                "address": provider.address,
                "total_books": textbooks.count()
            })
            results.append({
                "books_available": [
                    {
                        "title": tb.title,
                        "author": tb.author,
                        "price": str(tb.price),
                        "isbn": tb.isbn
                    }
                    for tb in textbooks[:10]
                ]
            })
        else:
            results.append({"info": "Provider not found."})
    #Find Cheaper Textbooks
    elif top_intent == "find_cheaper_textbooks":
        tname = entities.get("textbook_title", "")
        tid = entities.get("textbook_id", "")
        
        if tid:
            textbook = Textbook.objects.filter(textbook_id__iexact=tid).first()
            if textbook:
                tname = textbook.title
        
        if tname:
            # Find all books with similar titles
            similar_books = Textbook.objects.filter(title__icontains=tname).order_by("price")
            if similar_books:
                for tb in similar_books:
                    results.append({
                        "textbook_title": tb.title,
                        "author": tb.author,
                        "edition": tb.edition,
                        "price": str(tb.price),
                        "provider": tb.provider.provider_name,
                        "provider_contact": tb.provider.contact_number,
                        "isbn": tb.isbn
                    })
            else:
                results.append({"info": "No textbooks found with that title."})
        else:
            results.append({"info": "Please specify a textbook name or ID to search for cheaper options."})

    elif top_intent == "smart_suggestion":
        suggestion = call_ollama(
            f"Provide an academic suggestion based on: {user_message}. "
            f"Plain text only. End with 'Would you like more explanation?'"
        )
        return JsonResponse({"reply": suggestion.strip()})

    # No results found
    if not results:
        results.append({"info": "No matching data found."})

    suggestion_prompt = f"""
    You are a friendly and helpful academic assistant for students.
    Based on the student's question and the data provided, give a relevant and actionable tip or suggestion.
    
    Your response should:
    - Be conversational and encouraging
    - Provide practical advice related to the data
    - Be concise (2-3 sentences max)
    - Avoid generic advice; tailor it to the specific data
    - Use plain text only (no markdown, no formatting)
    
    Context:
    - If the data shows courses: Give study strategies, time management tips, or highlight important topics
    - If the data shows textbooks: Suggest how to use them effectively, compare editions, or find resources
    - If the data shows borrow/schedule info: Help them plan their studies or library visits
    - If the data shows providers: Suggest where to get books or how to save money
    - Always be supportive and positive in tone
    
    Student's question: "{user_message}"
    Relevant data: {json.dumps(results)}
    
    Provide a helpful suggestion now:
    """

    ai_suggestion = call_ollama(suggestion_prompt)
    ai_suggestion = ai_suggestion.replace("`", "").strip()

    results.append({"ai_suggestion": ai_suggestion})

   

    rewrite_prompt = f"""
    You are a friendly academic assistant chatbot. Convert the student's question and the data into a natural, helpful response.
    
    Guidelines:
    - Write in a conversational, warm tone like a helpful peer mentor
    - Start by directly answering the student's question with relevant data
    - Use specific information from the data to make the response valuable
    - If there's an AI suggestion in the data, incorporate it naturally at the end
    - Break information into short, digestible sentences
    - Avoid robotic language and be personable
    - Never use markdown, code blocks, asterisks, or special formatting
    - If no data is found, be encouraging and suggest helpful next steps
    - Keep the tone positive and supportive throughout
    
    Student's question: "{user_message}"
    Data to reference: {json.dumps(results)}
    
    Now write a natural, helpful response to the student:
    """

    final_answer = call_ollama(rewrite_prompt)
    final_answer = final_answer.replace("```", "").replace("`", "").strip()

    return JsonResponse({"reply": final_answer})


    
#---------------Authentication-----------------
def student_register(request):
    if request.method == "POST":
        first_name=request.POST["first_name"]
        last_name=request.POST["last_name"]
        username = request.POST["username"]
        password = request.POST["password"]
        email = request.POST["email"]
        student_id = request.POST["student_id"]

        student = get_object_or_404(Student, student_id=student_id)

        user = User.objects.create_user(username=username, password=password,first_name=first_name,last_name=last_name,email=email)
        StudentAccount.objects.create(user=user, student=student)
        if user:
            login(request, user)
            messages.success(request, "Registration successful!")
            return redirect("student_login")
        else:
            messages.error(request, "Registration failed. Please try again.")
            return redirect("student_register")

    return render(request, "auth/student_register.html",{"hide_header": True})

def student_login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(username=username, password=password)

        if user:
            login(request, user)
            messages.success(request, "Login successful!")
            return redirect("student_dashboard")
        else:
            messages.error(request, "Invalid credentials. Please try again.")

    return render(request, "auth/student_login.html",{"hide_header": True})

def instructor_login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(username=username, password=password)

        if user:
            # check if user is instructor
            if InstructorAccount.objects.filter(user=user).exists():
                login(request, user)
                messages.success(request, "Login successful!")
                return redirect("instructor_dashboard")
        else:
            messages.error(request, "Invalid credentials. Please try again.")

    return render(request, "auth/instructor_login.html",{"hide_header": True})

def instructor_register(request):
    if request.method == "POST":

        first_name = request.POST["first_name"]
        last_name = request.POST["last_name"]
        username = request.POST["username"]
        password = request.POST["password"]
        email = request.POST["email"]
        instructor_id = request.POST["instructor_id"]

        # 1. Get the Instructor record
        instructor = get_object_or_404(Instructor, instructor_id=instructor_id)

        # 2. Check if a Django User already uses the username
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken.")
            return redirect("instructor_register")

        # 3. Check if this instructor already has an InstructorAccount
        if InstructorAccount.objects.filter(instructor=instructor).exists():
            messages.error(request, "This instructor already has an account.")
            return redirect("instructor_register")

        # 4. Create Django User
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email
        )

        # 5. Create InstructorAccount linking user → instructor
        InstructorAccount.objects.create(
            user=user,
            instructor=instructor
        )

        messages.success(request, "Instructor registration successful!")
        return redirect("instructor_login")

    return render(request, "auth/instructor_register.html", {"hide_header": True})


def landing(request):
    return render(request, "auth/landing.html",{"hide_header": True})

def logout(request):
    auth_logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("landing")

@login_required
def instructor_dashboard(request):
    account = get_object_or_404(InstructorAccount, user=request.user)
    instructor = account.instructor

    # Sections taught by this instructor
    sections = Section.objects.filter(instructor=instructor)

    return render(request, "dashboard/instructor_dashboard.html", {
        "instructor": instructor,
        "sections": sections,
    })

def student_forgot_password(request):

    # Step 1 — show email input
    if request.method == "GET":
        return render(request, "auth/student_forgot_password.html", {
            "step": 1,
            "hide_header": True
        })

    email = request.POST.get("email")

    # Step 2 — user submitted email (no passwords yet)
    if "password1" not in request.POST:
        try:
            student = Student.objects.get(email=email)
            account = StudentAccount.objects.get(student=student)

            return render(request, "auth/student_forgot_password.html", {
                "step": 2,
                "student": student,
                "hide_header": True
            })

        except (Student.DoesNotExist, StudentAccount.DoesNotExist):
            messages.error(request, "No student found with that email.")
            return redirect("student_forgot_password")

    # Step 3 — user submitted new password
    p1 = request.POST.get("password1")
    p2 = request.POST.get("password2")

    if p1 != p2:
        messages.error(request, "Passwords do not match.")
        return redirect("student_forgot_password")

    student = Student.objects.get(email=email)
    account = StudentAccount.objects.get(student=student)
    user = account.user     # Get the actual Django User


    user.set_password(p1)
    user.save()

    messages.success(request, "Password reset successful! You can now log in.")
    return redirect("student_login")

def instructor_forgot_password(request):

    # Step 1 — show email input
    if request.method == "GET":
        return render(request, "auth/instructor_forgot_password.html", {
            "step": 1,
            "hide_header": True
        })

    email = request.POST.get("email")

    # Step 2 — user submitted email (no passwords yet)
    if "password1" not in request.POST:
        try:
            instructor = Instructor.objects.get(email=email)
            account = InstructorAccount.objects.get(instructor=instructor)

            return render(request, "auth/instructor_forgot_password.html", {
                "step": 2,
                "instructor": instructor,
                "hide_header": True
            })

        except (Instructor.DoesNotExist, InstructorAccount.DoesNotExist):
            messages.error(request, "No instructor found with that email.")
            return redirect("instructor_forgot_password")

    # Step 3 — user submitted new password
    p1 = request.POST.get("password1")
    p2 = request.POST.get("password2")

    if p1 != p2:
        messages.error(request, "Passwords do not match.")
        return redirect("instructor_forgot_password")

    instructor = Instructor.objects.get(email=email)
    account = InstructorAccount.objects.get(instructor=instructor)
    user = account.user  # linked Django User

    user.set_password(p1)
    user.save()

    messages.success(request, "Password reset successful! You can now log in.")
    return redirect("instructor_login")

@login_required
def modify_textbooks(request):
    instructor = request.user.instructoraccount.instructor
    sections = Section.objects.filter(instructor=instructor).select_related("course")

    return render(request, "instructors/modify_textbooks.html", {
        "sections": sections,
    })

@login_required
def edit_section_textbooks(request, section_id):
    account = get_object_or_404(InstructorAccount, user=request.user)
    instructor = account.instructor

    section = get_object_or_404(Section, section_id=section_id)

    # Security: ensure instructor teaches this section
    if section.instructor != instructor:
        messages.error(request, "You are not authorized to modify this section.")
        return redirect("instructor_dashboard")

    textbooks = Textbook.objects.all()
    assigned = SectionTextbook.objects.filter(section=section)

    if request.method == "POST":
        textbook_id = request.POST.get("textbook")
        requirement = request.POST.get("requirement")

        if not textbook_id:
            messages.error(request, "Please select a textbook.")
            return redirect("edit_section_textbooks", section_id=section_id)

        textbook_obj = get_object_or_404(Textbook, textbook_id=textbook_id)

        # Prevent duplicates
        if SectionTextbook.objects.filter(section=section, textbook=textbook_obj).exists():
            messages.error(request, "This textbook is already assigned.")
            return redirect("edit_section_textbooks", section_id=section_id)

        # CREATE NEW ENTRY IN THE DATABASE
        SectionTextbook.objects.create(
            section=section,
            textbook=textbook_obj,
            requirement_type=requirement,
        )

        messages.success(request, "Textbook successfully added.")
        return redirect("edit_section_textbooks", section_id=section_id)

    return render(request, "instructors/edit_section_textbooks.html", {
        "section": section,
        "textbooks": textbooks,
        "assigned": assigned,
    })
@login_required
def remove_textbook(request, st_id):
    st = get_object_or_404(SectionTextbook, id=st_id)

    account = get_object_or_404(InstructorAccount, user=request.user)
    instructor = account.instructor

    # Ensure security
    if st.section.instructor != instructor:
        messages.error(request, "You cannot remove textbooks from this section.")
        return redirect("instructor_dashboard")

    section_id = st.section.section_id

    # DELETE ROW FROM DATABASE
    st.delete()

    messages.success(request, "Textbook removed successfully.")
    return redirect("edit_section_textbooks", section_id=section_id)

@login_required
def instructor_edit_profile(request):
    instructor_account = request.user.instructoraccount
    instructor = instructor_account.instructor

    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        department = request.POST.get("department")

        # Basic validation
        if not name or not email:
            messages.error(request, "Name and email are required.")
            return redirect("instructor_edit_profile")

        # Email must be unique across instructor table (except their own)
        if Instructor.objects.filter(email=email).exclude(pk=instructor.pk).exists():
            messages.error(request, "This email is already used by another instructor.")
            return redirect("instructor_edit_profile")

        # Update instructor model
        instructor.name = name
        instructor.email = email
        instructor.phone = phone
        instructor.department = department
        instructor.save()

        # Update Django User email
        request.user.email = email
        request.user.save()

        messages.success(request, "Profile updated successfully!")
        return redirect("instructor_dashboard")

    context = {
        "instructor": instructor,
        "hide_header": False, 
    }
    return render(request, "instructors/instructor_edit_profile.html", context)

#------------------Student Dashboard-----------------------
@login_required
def student_dashboard(request):
    account = StudentAccount.objects.get(user=request.user)
    student = account.student

    # Sections enrolled
    sections = Section.objects.filter(
        enrollment__student=student
    ).select_related("course", "instructor")

    # Courses related to these sections
    courses = Course.objects.filter(
        section__enrollment__student=student
    ).distinct()

    # Textbooks assigned to the student's sections
    textbooks = Textbook.objects.filter(
        sectiontextbook__section__in=sections
    ).select_related("provider").distinct()

    # Providers from these textbooks
    providers = BookProvider.objects.filter(
        textbook__in=textbooks
    ).distinct()

    # Borrowed textbooks
    borrows = Borrow.objects.filter(student=student).select_related("textbook")

    # Summary stats
    stats = {
        "total_courses": courses.count(),
        "total_sections": sections.count(),
        "total_textbooks": textbooks.count(),
        "borrowed_count": borrows.count(),
    }

    # Recently added textbooks (latest by textbook_id)
    recent_textbooks = textbooks.order_by("-textbook_id")[:4]

    context = {
        "student": student,
        "stats": stats,
        "sections": sections,
        "courses": courses,
        "textbooks": textbooks,
        "providers": providers,
        "borrows": borrows,
        "recent_textbooks": recent_textbooks,
        "show_chatbot": True,
    }

    return render(request, "dashboard/student_dashboard.html", context)


@login_required
def student_courses(request):
    student = request.user.studentaccount.student
    courses = Course.objects.filter(section__enrollment__student=student).distinct()
    return render(request, "students/student_courses.html", {"courses": courses,"show_chatbot": True})

@login_required
def student_sections(request):
    student = request.user.studentaccount.student
    sections = Section.objects.filter(enrollment__student=student).select_related("course", "instructor")
    return render(request, "students/student_sections.html", {"sections": sections,"show_chatbot": True})

@login_required
def student_textbooks(request):
    student = request.user.studentaccount.student
    textbooks = Textbook.objects.filter(sectiontextbook__section__enrollment__student=student).distinct()
    return render(request, "students/student_textbooks.html", {"textbooks": textbooks,"show_chatbot": True})

@login_required
def student_instructors(request):
    student = request.user.studentaccount.student

    # all instructors teaching the student's enrolled sections
    instructors = Instructor.objects.filter(
        section__enrollment__student=student
    ).distinct()

    return render(request, "students/student_instructors.html", {
        "instructors": instructors,
        "show_chatbot": True,
    })


@login_required
def instructor_courses(request):
    instructor = request.user.instructoraccount.instructor
    courses = Course.objects.filter(section__instructor=instructor).distinct()
    return render(request, "instructors/instructor_courses.html", {"courses": courses})

@login_required
def instructor_sections(request):
    instructor = request.user.instructoraccount.instructor
    sections = Section.objects.filter(instructor=instructor).select_related("course")
    return render(request, "instructors/instructor_sections.html", {"sections": sections})

@login_required
def instructor_detail_view(request, instructor_id):
    instructor = get_object_or_404(Instructor, instructor_id=instructor_id)

    # All sections taught by this instructor (optional but useful)
    sections = Section.objects.filter(instructor=instructor).select_related("course")

    return render(request, "instructors/instructor_detail_view.html", {
        "instructor": instructor,
        "sections": sections,
    })

# ---------------Student-------------------
def student_list(request):
    students = Student.objects.all()
    return render(request, 'students/list.html', {'students': students})


def student_detail(request, student_id):
    student = get_object_or_404(Student, student_id=student_id)
    enrollments = Enrollment.objects.filter(student=student)
    borrows = Borrow.objects.filter(student=student)

    context = {
        'student': student,
        'enrollments': enrollments,
        'borrows': borrows,
    }
    return render(request, 'students/detail.html', context)


#----------------------Course-----------------------
def course_list(request):
    courses = Course.objects.all()
    return render(request, 'courses/list.html', {'courses': courses})


def course_detail(request, course_id):
    course = get_object_or_404(Course, course_id=course_id)
    sections = Section.objects.filter(course=course)
    course_textbooks = CourseTextbook.objects.filter(course=course)

    context = {
        'course': course,
        'sections': sections,
        'course_textbooks': course_textbooks,
    }
    return render(request, 'courses/detail.html', context)


# ------------------Section---------------------
def section_list(request):
    sections = Section.objects.all()
    return render(request, 'sections/list.html', {'sections': sections})


def section_detail(request, section_id):
    section = get_object_or_404(Section, section_id=section_id)
    section_textbooks = SectionTextbook.objects.filter(section=section)

    context = {
        'section': section,
        'section_textbooks': section_textbooks,
    }
    return render(request, 'sections/detail.html', context)


# ---------------------Textbook-----------------------
def textbook_list(request):
    textbooks = Textbook.objects.all()
    return render(request, 'textbooks/list.html', {'textbooks': textbooks})


def textbook_detail(request, textbook_id):
    textbook = get_object_or_404(Textbook, textbook_id=textbook_id)
    section_textbooks = SectionTextbook.objects.filter(textbook=textbook)
    provider=textbook.provider


    context = {
        'textbook': textbook,
        'section_textbooks': section_textbooks,
        'provider': provider,
    }
    return render(request, 'textbooks/detail.html', context)


# ----------------Providers------------------------
def provider_list(request):
    providers = BookProvider.objects.all()
    return render(request, 'providers/list.html', {'providers': providers})

def provider_detail(request, provider_id):
    provider = get_object_or_404(BookProvider, provider_id=provider_id)
    textbooks = Textbook.objects.filter(provider=provider)  # all books from this provider

    return render(request, 'providers/detail.html', {
        'provider': provider,
        'textbooks': textbooks,
    })
# ------------------Search----------------------------
from django.db.models import Q

def search(request):
    query = request.GET.get("q", "").strip()
    filter_by = request.GET.get("filter", "all")

    if query == "":
        return render(request, "search/no_results.html")

    # ============================================================
    # SMART RANKING
    # ============================================================
    def rank(item, field):
        text = str(getattr(item, field, "")).lower()
        q = query.lower()
        score = 0
        if text == q: score += 50
        if text.startswith(q): score += 25
        if q in text: score += 10
        if len(text.split()) > 1 and q in text.split(): score += 15
        return score

    user = request.user

    # ============================================================
    # STUDENT SEARCH RESULTS
    # ============================================================
    if user.is_authenticated and hasattr(user, "studentaccount"):
        student = user.studentaccount.student

        # Student's sections
        sections = Section.objects.filter(
            Q(enrollment__student=student) &
            (
                Q(course__course_name__icontains=query) |
                Q(instructor__name__icontains=query) |
                Q(section_id__icontains=query)
            )
        ).distinct()

        # Student's courses
        courses = Course.objects.filter(
            section__in=sections,
            course_name__icontains=query
        ).distinct()

        # Student's textbooks
        textbooks = Textbook.objects.filter(
            sectiontextbook__section__in=sections
        ).filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(isbn__icontains=query)
        ).distinct()

        # Providers related to student's textbooks
        providers = BookProvider.objects.filter(
            textbook__in=textbooks,
            provider_name__icontains=query
        ).distinct()

        # Instructors teaching student's sections
        instructors = Instructor.objects.filter(
            section__in=sections,
            name__icontains=query
        ).distinct()

        # Borrow records of this student
        borrows = Borrow.objects.filter(
            Q(student=student) &
            Q(textbook__title__icontains=query)
        ).distinct()

        # Section↔Textbook mapping
        section_textbooks = SectionTextbook.objects.filter(
            section__in=sections,
            textbook__title__icontains=query
        ).distinct()

        # Course↔Textbook mapping
        course_textbooks = CourseTextbook.objects.filter(
            course__in=courses,
            textbook__title__icontains=query
        ).distinct()

        enrollments = Enrollment.objects.filter(
            section__in=sections,
            student=student
        )

    # ============================================================
    # INSTRUCTOR SEARCH RESULTS
    # ============================================================
    elif user.is_authenticated and hasattr(user, "instructoraccount"):
        instructor = user.instructoraccount.instructor

        # Instructor's sections
        sections = Section.objects.filter(
            instructor=instructor
        ).filter(
            Q(section_id__icontains=query) |
            Q(course__course_name__icontains=query)
        ).distinct()

        # Instructor's courses
        courses = Course.objects.filter(
            section__in=sections,
            course_name__icontains=query
        ).distinct()

        # Students enrolled in instructor's sections
        enrollments = Enrollment.objects.filter(
            section__in=sections,
            student__name__icontains=query
        ).distinct()

        # Textbooks in instructor's courses
        textbooks = Textbook.objects.filter(
            sectiontextbook__section__in=sections
        ).filter(
            Q(title__icontains=query) |
            Q(author__icontains=query)
        ).distinct()

        # Providers relevant to instructor's textbooks
        providers = BookProvider.objects.filter(
            textbook__in=textbooks,
            provider_name__icontains=query
        ).distinct()

        # Section↔Textbook mapping
        section_textbooks = SectionTextbook.objects.filter(
            section__in=sections,
            textbook__title__icontains=query
        ).distinct()

        # Course↔Textbook mapping
        course_textbooks = CourseTextbook.objects.filter(
            course__in=courses,
            textbook__title__icontains=query
        ).distinct()

        instructors = []   # instructors don't search instructors
        borrows = []       # instructors should not see borrow history

    # ============================================================
    # GUEST USER SEARCH (NOT LOGGED IN)
    # ============================================================
    else:
        courses = Course.objects.filter(course_name__icontains=query)
        textbooks = Textbook.objects.filter(title__icontains=query)
        sections = section_textbooks = course_textbooks = providers = instructors = enrollments = borrows = []

    # ============================================================
    # RANKING (Better Results Order)
    # ============================================================
    courses = sorted(courses, key=lambda c: rank(c, "course_name"), reverse=True)
    textbooks = sorted(textbooks, key=lambda t: rank(t, "title"), reverse=True)

    # ============================================================
    # RENDER RESULTS
    # ============================================================
    return render(request, "search/results.html", {
        "query": query,
        "courses": courses,
        "sections": sections,
        "textbooks": textbooks,
        "providers": providers,
        "instructors": instructors,
        "enrollments": enrollments,
        "borrows": borrows,
        "section_textbooks": section_textbooks,
        "course_textbooks": course_textbooks,
    })


def search_suggest(request):
    query = request.GET.get("q", "").strip()

    if query == "":
        return JsonResponse({"results": []})

    results = []

    # Students
    for s in Student.objects.filter(name__icontains=query).values("name")[:5]:
        results.append({"type": "Student", "text": s["name"]})

    # Courses
    for c in Course.objects.filter(course_name__icontains=query).values("course_name")[:5]:
        results.append({"type": "Course", "text": c["course_name"]})

    # Textbooks
    for t in Textbook.objects.filter(title__icontains=query).values("title")[:5]:
        results.append({"type": "Textbook", "text": t["title"]})

    # Instructors
    for i in Instructor.objects.filter(name__icontains=query).values("name")[:5]:
        results.append({"type": "Instructor", "text": i["name"]})

    # Sections
    for s in Section.objects.filter(course__course_name__icontains=query).values("course__course_name")[:5]:
        results.append({"type": "Section", "text": s["course__course_name"]})

    # Providers
    for p in BookProvider.objects.filter(provider_name__icontains=query).values("provider_name")[:5]:
        results.append({"type": "Provider", "text": p["provider_name"]})

    # Borrow
    for b in Borrow.objects.filter(textbook__title__icontains=query).values("textbook__title")[:5]:
        results.append({"type": "Borrow Record", "text": b["textbook__title"]})

    # Enrollment
    for e in Enrollment.objects.filter(student__name__icontains=query).values("student__name")[:5]:
        results.append({"type": "Enrollment", "text": e["student__name"]})

    # SectionTextbook
    for st in SectionTextbook.objects.filter(textbook__title__icontains=query).values("textbook__title")[:5]:
        results.append({"type": "Section Textbook", "text": st["textbook__title"]})

    # CourseTextbook
    for ct in CourseTextbook.objects.filter(textbook__title__icontains=query).values("textbook__title")[:5]:
        results.append({"type": "Course Textbook", "text": ct["textbook__title"]})

    return JsonResponse({"results": results})
