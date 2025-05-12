from django.urls import path
from django.contrib import admin
from . import views

urlpatterns = [

    # Home
    path('', views.home, name='home'),
    path('admin/', admin.site.urls),

    # Authentication & Signup
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('organization-signup/', views.organization_signup, name='organization_signup'),
    path('government-signup/', views.government_signup, name='government_signup'),
    path('user/signup/', views.user_signup, name='user_signup'),
    path('user/login/', views.user_login_view, name='user_login'),
    path('user/logout/', views.user_logout, name='user_logout'),

    # Dashboards
    path('dashboard/', views.organization_dashboard, name='dashboard'),
    path('state_dashboard/', views.state_government_dashboard, name='state_dashboard'),
    path('user/dashboard/', views.user_dashboard, name='user_dashboard'),

    # Organization Fund Requests to Government
    path('request-funds/', views.request_funds, name='request_funds'),
    path('review-fund-requests/<int:request_id>/', views.review_fund_requests, name='review_fund_requests'),
    # path('approve-reject/<int:request_id>/<str:status>/', views.approve_or_reject_fund, name='approve_or_reject_fund'),

    # User Fund Requests to Organization
    path('user/request-fund/', views.fund_request, name='user_fund_request'),
    # path('user-fund-request/<int:request_id>/<str:action>/', views.approve_or_reject_user_fund, name='approve_or_reject_user_fund'),
    # Blockchain Transaction Info
    path('transaction/<str:txn_hash>/', views.get_transaction_details, name='get_transaction_details'),
    path('approve-user-request/<int:request_id>/<str:action>/', views.approve_or_reject_user_fund, name='approve_or_reject_user_fund')

    
    
]
