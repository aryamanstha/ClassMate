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
    path("student/borrow/request/", views.student_request_borrow, name="student_request_borrow"),
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

    # Admin dashboard URLs
    path("admin/login/", views.admin_login, name="admin_login"),
    path("admin/", views.admin_dashboard, name="admin_dashboard"),
    path("admin/instructor-approvals/", views.admin_instructor_approvals, name="admin_instructor_approvals"),
    path("admin/instructor-approve/<int:instructor_account_id>/", views.admin_approve_instructor, name="admin_approve_instructor"),
    path("admin/instructor-reject/<int:instructor_account_id>/", views.admin_reject_instructor, name="admin_reject_instructor"),
    path("admin/students/", views.admin_students, name="admin_students"),
    path("admin/student/<str:student_id>/", views.admin_student_detail, name="admin_student_detail"),
    path("admin/student/<str:student_id>/delete/", views.admin_delete_student, name="admin_delete_student"),
    path("admin/instructors/", views.admin_instructors, name="admin_instructors"),
    path("admin/instructor/<str:instructor_id>/", views.admin_instructor_detail, name="admin_instructor_detail"),
    path("admin/instructor/<str:instructor_id>/delete/", views.admin_delete_instructor, name="admin_delete_instructor"),
    path("admin/courses/", views.admin_courses, name="admin_courses"),
    path("admin/course/<str:course_id>/", views.admin_course_detail, name="admin_course_detail"),
    path("admin/course/<str:course_id>/delete/", views.admin_delete_course, name="admin_delete_course"),
    path("admin/course/<str:course_id>/textbook/<str:textbook_id>/remove/", views.admin_remove_course_textbook, name="admin_remove_course_textbook"),
    path("admin/sections/", views.admin_sections, name="admin_sections"),
    path("admin/section/<str:section_id>/", views.admin_section_detail, name="admin_section_detail"),
    path("admin/section/<str:section_id>/delete/", views.admin_delete_section, name="admin_delete_section"),
    path("admin/textbooks/", views.admin_textbooks, name="admin_textbooks"),
    path("admin/textbook/<str:textbook_id>/", views.admin_textbook_detail, name="admin_textbook_detail"),
    path("admin/textbook/<str:textbook_id>/delete/", views.admin_delete_textbook, name="admin_delete_textbook"),
    path("admin/providers/", views.admin_providers, name="admin_providers"),
    path("admin/provider/<str:provider_id>/", views.admin_provider_detail, name="admin_provider_detail"),
    path("admin/provider/<str:provider_id>/delete/", views.admin_delete_provider, name="admin_delete_provider"),
    path("admin/borrowed-textbooks/", views.admin_borrowed_textbooks, name="admin_borrowed_textbooks"),
    path("admin/borrow/<int:borrow_id>/", views.admin_borrow_detail, name="admin_borrow_detail"),
    path("admin/borrow/<int:borrow_id>/approve/", views.admin_approve_borrow, name="admin_approve_borrow"),
    path("admin/borrow/<int:borrow_id>/reject/", views.admin_reject_borrow, name="admin_reject_borrow"),
    path("admin/borrow/<int:borrow_id>/delete/", views.admin_delete_borrow, name="admin_delete_borrow"),
    path("admin/user-accounts/", views.admin_user_accounts, name="admin_user_accounts"),
    path("admin/user/<int:user_id>/", views.admin_user_detail, name="admin_user_detail"),
    path("admin/user/<int:user_id>/reset-password/", views.admin_reset_user_password, name="admin_reset_user_password"),
    path("admin/user/<int:user_id>/disable/", views.admin_disable_user, name="admin_disable_user"),
    path("admin/user/<int:user_id>/enable/", views.admin_enable_user, name="admin_enable_user"),
    path("admin/user/<int:user_id>/delete/", views.admin_delete_user, name="admin_delete_user"),
    path("admin/user/<int:user_id>/grant-admin/", views.admin_grant_admin_access, name="admin_grant_admin_access"),
    path("admin/user/<int:user_id>/revoke-admin/", views.admin_revoke_admin_access, name="admin_revoke_admin_access"),
]
