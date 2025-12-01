from django.shortcuts import render, get_object_or_404
from .models import (
    Student, Instructor, Course, Section, Textbook,
    BookProvider, CourseTextbook, SectionTextbook,
    Enrollment, Borrow, StudentAccount, InstructorAccount
)
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth import logout as auth_logout

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
        "sections": sections
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
    }

    return render(request, "dashboard/student_dashboard.html", context)


@login_required
def student_courses(request):
    student = request.user.studentaccount.student
    courses = Course.objects.filter(section__enrollment__student=student).distinct()
    return render(request, "students/student_courses.html", {"courses": courses})

@login_required
def student_sections(request):
    student = request.user.studentaccount.student
    sections = Section.objects.filter(enrollment__student=student).select_related("course", "instructor")
    return render(request, "students/student_sections.html", {"sections": sections})

@login_required
def student_textbooks(request):
    student = request.user.studentaccount.student
    textbooks = Textbook.objects.filter(sectiontextbook__section__enrollment__student=student).distinct()
    return render(request, "students/student_textbooks.html", {"textbooks": textbooks})

@login_required
def student_instructors(request):
    student = request.user.studentaccount.student

    # all instructors teaching the student's enrolled sections
    instructors = Instructor.objects.filter(
        section__enrollment__student=student
    ).distinct()

    return render(request, "students/student_instructors.html", {
        "instructors": instructors
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
        "sections": sections
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
