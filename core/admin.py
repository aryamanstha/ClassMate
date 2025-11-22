from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(Student)
admin.site.register(Instructor)
admin.site.register(Course)
admin.site.register(Section)
admin.site.register(BookProvider)
admin.site.register(Textbook)
admin.site.register(CourseTextbook)
admin.site.register(SectionTextbook)
admin.site.register(Enrollment)
admin.site.register(Borrow)