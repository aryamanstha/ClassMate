from django.urls import path
from . import views

urlpatterns = [
    # path('', views.dashboard, name='dashboard'),
    path("", views.landing, name="landing"),
    # Chatbot
    path("chatbot/respond/", views.chatbot_respond, name="chatbot_respond"),
    #logout
    path('logout/', views.logout, name='logout'),
    # student auth
    path("student/login/", views.student_login, name="student_login"),
    path("student/register/", views.student_register, name="student_register"),
    path("student/forgot-password/", views.student_forgot_password, name="student_forgot_password"),

    # instructor
    path("instructor/login/", views.instructor_login, name="instructor_login"),
    path("instructor/register/", views.instructor_register, name="instructor_register"),
    path("instructor/forgot-password/", views.instructor_forgot_password, name="instructor_forgot_password"),
    path("instructor/section/<str:section_id>/edit/",views.edit_section_textbooks,name="edit_section_textbooks"),
    path("instructor/section/textbook/<int:st_id>/remove/", views.remove_textbook, name="remove_textbook"),



    # dashboards
    path("student/dashboard/", views.student_dashboard, name="student_dashboard"),
    path("instructor/dashboard/", views.instructor_dashboard, name="instructor_dashboard"),
    path('search/', views.search, name='search'),
    path("search/suggest/", views.search_suggest, name="search_suggest"),

    # Students
    path('students/', views.student_list, name='student_list'),
    path('students/<str:student_id>/', views.student_detail, name='student_detail'),

    # Courses
    path('courses/', views.course_list, name='course_list'),
    path('courses/<str:course_id>/', views.course_detail, name='course_detail'),

    # Sections
    path('sections/', views.section_list, name='section_list'),
    path('sections/<str:section_id>/', views.section_detail, name='section_detail'),

    # Textbooks
    path('textbooks/', views.textbook_list, name='textbook_list'),
    path('textbooks/<str:textbook_id>/', views.textbook_detail, name='textbook_detail'),

    # Providers
    path('providers/', views.provider_list, name='provider_list'),
    path('providers/<str:provider_id>/',views.provider_detail, name='provider_detail'),

    # Student personalized pages
    path("student/courses/", views.student_courses, name="student_courses"),
    path("student/sections/", views.student_sections, name="student_sections"),
    path("student/textbooks/", views.student_textbooks, name="student_textbooks"),
    # Student instructors
    path("student/instructors/", views.student_instructors, name="student_instructors"),
    path("student/instructor/<str:instructor_id>/", views.instructor_detail_view, name="instructor_detail_view"),
    
    # Instructor personalized pages
    path("instructor/courses/", views.instructor_courses, name="instructor_courses"),
    path("instructor/sections/", views.instructor_sections, name="instructor_sections"),
    path("instructor/modify-textbooks/", views.modify_textbooks, name="modify_textbooks"),
    path("instructor/add-textbook/", views.add_textbook, name="add_textbook"),
    # Instructor profile
    path("instructor/profile/edit/", views.instructor_edit_profile, name="instructor_edit_profile"),



]

