from django.db import models
from django.contrib.auth.models import User
import uuid


def generate_student_id():
    # short unique id like STUxxxx (6 hex chars)
    return f"STU{uuid.uuid4().hex[:6].upper()}"


def generate_instructor_id():
    return f"INS{uuid.uuid4().hex[:6].upper()}"


def generate_provider_id():
    # Provider ID like PRVxxxx (6 hex chars)
    return f"PRV{uuid.uuid4().hex[:6].upper()}"


def generate_textbook_id():
    # Textbook ID like TXBxxxx (6 hex chars)
    return f"TXB{uuid.uuid4().hex[:6].upper()}"


class Student(models.Model):
    student_id = models.CharField(max_length=12, primary_key=True, default=generate_student_id, editable=False)
    name = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    # additional address fields
    city = models.CharField(max_length=50, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    zip_code = models.CharField(max_length=12, blank=True, null=True)
    # store password hash only if required by professor (do NOT store plaintext)
    password_hash = models.CharField(max_length=128, blank=True, null=True)

    def __str__(self):
        return self.name

class Instructor(models.Model):
    instructor_id = models.CharField(max_length=12, primary_key=True, default=generate_instructor_id, editable=False)
    name = models.CharField(max_length=50)
    department = models.CharField(max_length=30)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    city = models.CharField(max_length=50, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    zip_code = models.CharField(max_length=12, blank=True, null=True)
    password_hash = models.CharField(max_length=128, blank=True, null=True)

    def __str__(self):
        return self.name


class Course(models.Model):
    course_id = models.CharField(max_length=10, primary_key=True)
    course_name = models.CharField(max_length=75)
    description = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.course_id} - {self.course_name}"


class Section(models.Model):
    section_id = models.CharField(max_length=20, primary_key=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE)
    year = models.IntegerField()
    semester = models.CharField(max_length=6)

    def __str__(self):
        return self.section_id


class BookProvider(models.Model):
    provider_id = models.CharField(max_length=10, primary_key=True, default=generate_provider_id, editable=False)
    provider_name = models.CharField(max_length=75)
    contact_number = models.CharField(max_length=15)
    address = models.CharField(max_length=100)

    def __str__(self):
        return self.provider_name


class Textbook(models.Model):
    textbook_id = models.CharField(max_length=10, primary_key=True, default=generate_textbook_id, editable=False)
    provider = models.ForeignKey(BookProvider, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    author = models.CharField(max_length=75)
    edition = models.CharField(max_length=10)
    isbn = models.CharField(max_length=13, unique=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return self.title


class CourseTextbook(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    textbook = models.ForeignKey(Textbook, on_delete=models.CASCADE)


class SectionTextbook(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    textbook = models.ForeignKey(Textbook, on_delete=models.CASCADE)
    requirement_type = models.CharField(max_length=30)


class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)


class Borrow(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    textbook = models.ForeignKey(Textbook, on_delete=models.CASCADE)
    status = models.CharField(max_length=30)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.end_date and self.start_date and self.end_date <= self.start_date:
            raise ValidationError("End date must be after the start date.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class StudentAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student = models.OneToOneField(Student, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username


class InstructorAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    instructor = models.OneToOneField(Instructor, on_delete=models.CASCADE)
    # admin approval required for instructors
    approved = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username