# public/views.py

from django.shortcuts import render, redirect
from django.db.models import Q
from django.utils.dateparse import parse_date
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.generic import TemplateView
from django.contrib import messages
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination
from .models import Notice, AdmissionApplication
from .serializers import (
    NoticeListSerializer,
    AdmissionApplicationCreateSerializer,
    UserRegistrationSerializer,
)
from .forms import AdmissionApplicationForm, UserRegistrationForm

# Rate limiting setup
try:
    from django_ratelimit.decorators import ratelimit
    RATELIMIT_AVAILABLE = True
except ImportError:
    RATELIMIT_AVAILABLE = False
    ratelimit = lambda *args, **kwargs: lambda func: func

def conditional_ratelimit(rate="5/h"):
    """Apply rate limiting only if enabled in settings"""
    def decorator(view_class):
        if RATELIMIT_AVAILABLE and getattr(settings, "RATELIMIT_ENABLE", False):
            return method_decorator(ratelimit(key="ip", rate=rate, method="POST", block=True), name="post")(view_class)
        return view_class
    return decorator


# =============================================================================
# API VIEWS
# =============================================================================


class NoticeListPagination(PageNumberPagination):
    """Custom pagination for notice listing."""

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50


class NoticeListAPIView(generics.ListAPIView):
    """
    API endpoint for listing published notices.
    Supports search by title/content and date filtering.
    """

    serializer_class = NoticeListSerializer
    permission_classes = [AllowAny]
    pagination_class = NoticeListPagination

    def get_queryset(self):
        """Get published notices with optional search and date filtering."""
        queryset = Notice.objects.published().select_related("created_by")

        # Search functionality
        search_query = self.request.query_params.get("search", None)
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) | Q(content__icontains=search_query)
            )

        # Date filtering
        date_from = self.request.query_params.get("date_from", None)
        date_to = self.request.query_params.get("date_to", None)

        if date_from:
            try:
                parsed_date_from = parse_date(date_from)
                if parsed_date_from:
                    queryset = queryset.filter(date_created__date__gte=parsed_date_from)
            except ValueError:
                pass

        if date_to:
            try:
                parsed_date_to = parse_date(date_to)
                if parsed_date_to:
                    queryset = queryset.filter(date_created__date__lte=parsed_date_to)
            except ValueError:
                pass

        return queryset.order_by("-date_created")


@conditional_ratelimit(rate="5/h")
class AdmissionApplicationCreateAPIView(generics.CreateAPIView):
    """API endpoint for creating admission applications with rate limiting."""
    serializer_class = AdmissionApplicationCreateSerializer
    permission_classes = [AllowAny]
    queryset = AdmissionApplication.objects.all()

    def create(self, request, *args, **kwargs):
        """Create admission application."""
        import logging
        logger = logging.getLogger(__name__)
        client_ip = self._get_client_ip(request)
        logger.info(f"Admission application submission from IP: {client_ip}")

        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error": "Validation failed", "details": serializer.errors}, 
                          status=status.HTTP_400_BAD_REQUEST)

        try:
            application = serializer.save()
            logger.info(f"Application created - ID: {application.id}, Student: {application.student_name}")
            return Response({
                "success": True,
                "message": "Application submitted successfully! We will contact you within 3-5 business days.",
                "data": {
                    "application_id": application.id,
                    "student_name": application.student_name,
                    "enrolled_class": application.enrolled_class,
                    "status": application.get_status_display(),
                    "date_submitted": application.date_submitted.strftime("%B %d, %Y at %I:%M %p"),
                }
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating application: {str(e)}")
            if "unique constraint" in str(e).lower():
                return Response({"error": "Duplicate application", 
                               "details": {"general": ["An application with this information already exists."]}}, 
                              status=status.HTTP_400_BAD_REQUEST)
            return Response({"error": "Submission failed", "details": {"general": ["Please try again later."]}}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        return x_forwarded_for.split(",")[0] if x_forwarded_for else request.META.get("REMOTE_ADDR")


@conditional_ratelimit(rate="3/h")
class UserRegistrationAPIView(generics.CreateAPIView):
    """API endpoint for user registration with rate limiting."""
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        """Create user account."""
        import logging
        logger = logging.getLogger(__name__)
        client_ip = self._get_client_ip(request)
        logger.info(f"User registration attempt from IP: {client_ip}")

        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error": "Registration failed", "details": serializer.errors}, 
                          status=status.HTTP_400_BAD_REQUEST)

        try:
            user = serializer.save()
            logger.info(f"User created - Username: {user.username}")
            return Response({
                "success": True,
                "message": "User registered successfully",
                "user": {
                    "username": user.username,
                    "email": user.email,
                    "role": user.role.name if user.role else "Guest",
                }
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return Response({"error": "Registration failed", 
                           "details": {"general": ["An error occurred during registration. Please try again."]}}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        return x_forwarded_for.split(",")[0] if x_forwarded_for else request.META.get("REMOTE_ADDR")


# =============================================================================
# TEMPLATE VIEWS
# =============================================================================


class HomeView(TemplateView):
    """Home page view displaying recent published notices."""
    template_name = "public/home.html"

    def get_context_data(self, **kwargs):
        """Add recent published notices to the template context."""
        context = super().get_context_data(**kwargs)
        context.update({
            "recent_notices": Notice.objects.recent_published(limit=5),
            "total_notices": Notice.objects.published().count(),
            "page_title": "Welcome to School Management System",
            "page_description": "Stay updated with the latest school notices and announcements.",
        })
        return context


class NoticeListView(TemplateView):
    """Notice list template view with search functionality and pagination."""

    template_name = "public/notices.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get search parameters from request
        search_query = self.request.GET.get("search", "").strip()
        date_from = self.request.GET.get("date_from", "").strip()
        date_to = self.request.GET.get("date_to", "").strip()

        # Start with published notices
        notices = Notice.objects.published().select_related("created_by")

        # Apply search filter
        if search_query:
            notices = notices.filter(
                Q(title__icontains=search_query) | Q(content__icontains=search_query)
            )

        # Apply date filters
        if date_from:
            try:
                parsed_date_from = parse_date(date_from)
                if parsed_date_from:
                    notices = notices.filter(date_created__date__gte=parsed_date_from)
            except ValueError:
                pass

        if date_to:
            try:
                parsed_date_to = parse_date(date_to)
                if parsed_date_to:
                    notices = notices.filter(date_created__date__lte=parsed_date_to)
            except ValueError:
                pass

        # Order by creation date (newest first)
        notices = notices.order_by("-date_created")

        # Implement pagination
        paginator = Paginator(notices, 10)  # Show 10 notices per page
        page = self.request.GET.get("page")

        try:
            notices_page = paginator.page(page)
        except PageNotAnInteger:
            notices_page = paginator.page(1)
        except EmptyPage:
            notices_page = paginator.page(paginator.num_pages)

        # Add context data
        context.update(
            {
                "notices": notices_page,
                "search_query": search_query,
                "date_from": date_from,
                "date_to": date_to,
                "total_notices": paginator.count,
                "page_title": "School Notices",
                "page_description": "Browse all published school notices and announcements",
                "has_filters": bool(search_query or date_from or date_to),
            }
        )

        return context


class LoginView(TemplateView):
    """User login template view."""

    template_name = "public/login.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": "Login",
                "page_description": "Login to access your account and dashboard.",
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        """Handle login form submission with session-based authentication."""
        from django.contrib.auth import authenticate, login
        from django.http import JsonResponse
        import json

        try:
            # Parse JSON data
            data = json.loads(request.body)
            username = data.get("username")
            password = data.get("password")

            if not username or not password:
                return JsonResponse(
                    {"error": "Username and password are required"}, status=400
                )

            # Authenticate user
            user = authenticate(request, username=username, password=password)

            if user is not None:
                if user.is_active:
                    # Log the user in (creates session)
                    login(request, user)

                    # Return success response with redirect URL
                    # Check if user has permission to view dashboard
                    redirect_url = "/dashboard/" if user.has_role_permission('can_view_dashboard') else "/"

                    return JsonResponse(
                        {
                            "success": True,
                            "redirect_url": redirect_url,
                            "user": {
                                "username": user.username,
                                "role": user.role.name if user.role else "Guest",
                                "is_admin_or_above": user.is_admin_or_above(),
                            },
                        }
                    )
                else:
                    return JsonResponse({"error": "Account is disabled"}, status=400)
            else:
                return JsonResponse(
                    {"error": "Invalid username or password"}, status=400
                )

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"Login failed: {str(e)}"}, status=500)


class LogoutView(TemplateView):
    """User logout view."""

    def get(self, request, *args, **kwargs):
        """Handle logout via GET request"""
        from django.contrib.auth import logout

        logout(request)
        return redirect("public:home")

    def post(self, request, *args, **kwargs):
        """Handle logout via POST request"""
        from django.contrib.auth import logout
        from django.http import JsonResponse

        logout(request)
        return JsonResponse({"success": True, "redirect_url": "/"})


class AdmissionApplicationCreateView(TemplateView):
    """Admission application form view with comprehensive form handling."""

    template_name = "public/admission_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": "Admission Application",
                "page_description": "Apply for admission to our school with our secure online application form.",
            }
        )
        return context

    def get(self, request, *args, **kwargs):
        """Display the admission application form"""
        context = self.get_context_data(**kwargs)
        context["form"] = AdmissionApplicationForm()

        # Check for success message
        if request.GET.get("success") == "1":
            context["success_message"] = {
                "title": "Application Submitted Successfully!",
                "message": "Thank you for your application. We have received your admission application and will review it within 3-5 business days.",
            }

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        """Process the admission application form submission"""
        form = AdmissionApplicationForm(request.POST)
        context = self.get_context_data(**kwargs)
        context["form"] = form

        if form.is_valid():
            try:
                application = form.save()
                messages.success(
                    request,
                    f"Your admission application has been submitted successfully! "
                    f"Application ID: {application.id}. "
                    f"We will contact you within 3-5 business days.",
                )
                return redirect(f"{request.path}?success=1")
            except Exception as e:
                if "unique constraint" in str(e).lower():
                    form.add_error(
                        None, "An application with this information already exists."
                    )
                else:
                    form.add_error(
                        None, "We encountered a technical issue. Please try again."
                    )

        return self.render_to_response(context)


class UserRegistrationView(TemplateView):
    """User registration view with comprehensive form handling."""

    template_name = "public/register.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": "User Registration",
                "page_description": "Create your account to access additional features of our school management system.",
            }
        )
        return context

    def get(self, request, *args, **kwargs):
        """Display the user registration form"""
        context = self.get_context_data(**kwargs)
        context["form"] = UserRegistrationForm()

        # Check for success message
        if request.GET.get("success") == "1":
            context["success_message"] = {
                "title": "Registration Successful!",
                "message": "Your account has been created successfully. You can now log in with your credentials.",
            }

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        """Process the user registration form submission"""
        form = UserRegistrationForm(request.POST)
        context = self.get_context_data(**kwargs)
        context["form"] = form

        if form.is_valid():
            try:
                user = form.save()
                messages.success(
                    request,
                    f"Your account has been created successfully! "
                    f"You can now log in with username: {user.username}",
                )
                return redirect(f"{request.path}?success=1")
            except Exception as e:
                if "unique constraint" in str(e).lower():
                    form.add_error(
                        None, "An account with this information already exists."
                    )
                else:
                    form.add_error(
                        None, "We encountered a technical issue. Please try again."
                    )

        return self.render_to_response(context)
