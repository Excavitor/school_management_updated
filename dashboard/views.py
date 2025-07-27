"""Clean and optimized views for dashboard app."""

import csv
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from accounts.permissions import (
    IsAdminOrSuperAdminPermission, 
    IsSuperAdminPermission,
    NoticeManagementPermission,
    ApplicationManagementPermission,
    CanViewUserPermission,
    CanAddUserPermission,
    CanUpdateUserPermission,
    CanDeleteUserPermission,
    CanViewRolePermission,
    CanAddRolePermission,
    CanUpdateRolePermission,
    CanDeleteRolePermission,
    CanExportDataPermission
)
from accounts.models import CustomUser, Role, validate_bangladeshi_phone
from public.models import Notice, AdmissionApplication
from .serializers import (
    NoticeManagementSerializer,
    AdmissionApplicationManagementSerializer,
    UserManagementSerializer,
    UserProfileSerializer,
    RoleManagementSerializer,
    BulkActionSerializer,
)


class DashboardPagination(PageNumberPagination):
    """Custom pagination for dashboard."""

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class DashboardStatsAPIView(APIView):
    """API view for dashboard statistics."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get dashboard statistics."""
        try:
            stats = {
                "total_applications": AdmissionApplication.objects.count(),
                "total_notices": Notice.objects.count(),
                "pending_applications": AdmissionApplication.objects.filter(
                    status="pending"
                ).count(),
                "published_notices": Notice.objects.filter(published=True).count(),
                "total_users": CustomUser.objects.count(),
                "recent_applications": self.get_recent_applications(),
            }
            return Response(stats)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_recent_applications(self):
        """Get recent applications."""
        recent = AdmissionApplication.objects.order_by("-date_submitted")[:5]
        return [
            {
                "id": app.id,
                "student_name": app.student_name,
                "enrolled_class": app.enrolled_class,
                "status": app.status,
                "date_submitted": app.date_submitted.isoformat(),
            }
            for app in recent
        ]


# Frontend Views
class DashboardHomeView(LoginRequiredMixin, TemplateView):
    """Dashboard home page."""

    template_name = "dashboard/home.html"

    def dispatch(self, request, *args, **kwargs):
        # Check if user has permission to view dashboard
        if not request.user.has_role_permission("can_view_dashboard"):
            messages.error(
                request,
                "Access denied. You don't have permission to view the dashboard.",
            )
            return redirect("public:home")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add statistics based on user permissions
        if self.request.user.has_role_permission("can_view_application"):
            context.update(
                {
                    "total_applications": AdmissionApplication.objects.count(),
                    "pending_applications": AdmissionApplication.objects.filter(
                        status="pending"
                    ).count(),
                    "recent_applications": AdmissionApplication.objects.order_by(
                        "-date_submitted"
                    )[:5],
                    "application_status_breakdown": {
                        "pending": AdmissionApplication.objects.filter(
                            status="pending"
                        ).count(),
                        "accepted": AdmissionApplication.objects.filter(
                            status="accepted"
                        ).count(),
                        "rejected": AdmissionApplication.objects.filter(
                            status="rejected"
                        ).count(),
                    },
                }
            )

        if self.request.user.has_role_permission("can_view_notice"):
            context.update(
                {
                    "total_notices": Notice.objects.count(),
                }
            )

        if self.request.user.has_role_permission("can_view_user"):
            user_stats = {}
            for role in ["SuperAdmin", "Admin", "Teacher", "Guest"]:
                user_stats[role] = CustomUser.objects.filter(role__name=role).count()
            user_stats["total"] = CustomUser.objects.count()
            context["user_statistics"] = user_stats

        return context


class NoticeListView(LoginRequiredMixin, TemplateView):
    """Notice management page."""

    template_name = "dashboard/notices/list.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_role_permission("can_view_notice"):
            messages.error(
                request, "Access denied. You don't have permission to view notices."
            )
            return redirect("dashboard:home")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        notices = Notice.objects.select_related("created_by").all()

        # Get search and filter parameters
        search_query = self.request.GET.get("search", "").strip()
        published_filter = self.request.GET.get("published", "")
        ordering = self.request.GET.get("ordering", "-date_created")

        # Apply search filter
        if search_query:
            notices = notices.filter(
                Q(title__icontains=search_query) | Q(content__icontains=search_query)
            )

        # Apply published filter
        if published_filter == "true":
            notices = notices.filter(published=True)
        elif published_filter == "false":
            notices = notices.filter(published=False)

        # Apply ordering
        valid_orderings = [
            "-date_created",
            "date_created",
            "title",
            "-title",
            "-date_updated",
            "date_updated",
        ]
        if ordering in valid_orderings:
            notices = notices.order_by(ordering)
        else:
            notices = notices.order_by("-date_created")

        # Pagination
        paginator = Paginator(notices, 10)
        page = self.request.GET.get("page")
        context["notices"] = paginator.get_page(page)

        # Add search context for form persistence
        context["search_query"] = search_query
        context["published_filter"] = published_filter
        context["ordering"] = ordering

        return context


class ApplicationListView(LoginRequiredMixin, TemplateView):
    """Application management page."""

    template_name = "dashboard/applications/list.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_role_permission("can_view_application"):
            messages.error(
                request,
                "Access denied. You don't have permission to view applications.",
            )
            return redirect("dashboard:home")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        applications = AdmissionApplication.objects.all()

        # Get search and filter parameters
        search_query = self.request.GET.get("search", "").strip()
        status_filter = self.request.GET.get("status", "")
        ordering = self.request.GET.get("ordering", "-date_submitted")

        # Apply search filter
        if search_query:
            applications = applications.filter(
                Q(student_name__icontains=search_query)
                | Q(guardian_name__icontains=search_query)
                | Q(guardian_email__icontains=search_query)
                | Q(guardian_mobile__icontains=search_query)
                | Q(enrolled_class__icontains=search_query)
            )

        # Apply status filter
        if status_filter and status_filter != "all":
            applications = applications.filter(status=status_filter)

        # Apply ordering
        valid_orderings = [
            "-date_submitted",
            "date_submitted",
            "student_name",
            "-student_name",
            "status",
            "-status",
            "enrolled_class",
            "-enrolled_class",
        ]
        if ordering in valid_orderings:
            applications = applications.order_by(ordering)
        else:
            applications = applications.order_by("-date_submitted")
        # Pagination
        paginator = Paginator(applications, 10)
        page = self.request.GET.get("page")
        context["applications"] = paginator.get_page(page)

        # Add search context for form persistence
        context["search_query"] = search_query
        context["status_filter"] = status_filter
        context["ordering"] = ordering
        context["status_choices"] = AdmissionApplication.STATUS_CHOICES

        return context


class UserListView(LoginRequiredMixin, TemplateView):
    """User management page."""

    template_name = "dashboard/users/user_list.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_role_permission("can_view_user"):
            messages.error(
                request, "Access denied. You don't have permission to view users."
            )
            return redirect("dashboard:home")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        users = CustomUser.objects.select_related("role").all()

        # Get search and filter parameters
        search_query = self.request.GET.get("search", "").strip()
        role_filter = self.request.GET.get("role", "")
        ordering = self.request.GET.get("ordering", "-date_joined")

        # Apply search filter
        if search_query:
            users = users.filter(
                Q(username__icontains=search_query)
                | Q(email__icontains=search_query)
                | Q(first_name__icontains=search_query)
                | Q(last_name__icontains=search_query)
                | Q(phone_number__icontains=search_query)
            )

        # Apply role filter
        if role_filter:
            users = users.filter(role__name=role_filter)

        # Apply ordering
        valid_orderings = [
            "-date_joined",
            "date_joined",
            "username",
            "-username",
            "email",
            "-email",
        ]
        if ordering in valid_orderings:
            users = users.order_by(ordering)
        else:
            users = users.order_by("-date_joined")
        # Pagination
        paginator = Paginator(users, 10)
        page = self.request.GET.get("page")
        context["users"] = paginator.get_page(page)

        # Add search context for form persistence
        context["search_query"] = search_query
        context["role_filter"] = role_filter
        context["ordering"] = ordering
        context["roles"] = Role.objects.all().order_by("name")

        return context


class UserProfileView(LoginRequiredMixin, TemplateView):
    """User profile page."""

    template_name = "dashboard/users/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_obj"] = self.request.user
        return context


class NoticeCreateView(LoginRequiredMixin, TemplateView):
    """Notice creation page."""

    template_name = "dashboard/notices/create.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_role_permission("can_add_notice"):
            messages.error(
                request, "Access denied. You don't have permission to create notices."
            )
            return redirect("dashboard:home")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Handle notice creation form submission."""
        # Get form data
        title = request.POST.get("title", "").strip()
        content = request.POST.get("content", "").strip()
        published = request.POST.get("published") == "on"

        errors = {}

        # Validate required fields
        if not title:
            errors["title"] = "Title is required."

        if not content:
            errors["content"] = "Content is required."

        # If there are errors, return to form with errors
        if errors:
            context = self.get_context_data(**kwargs)
            context["errors"] = errors
            context["form_data"] = request.POST
            return render(request, self.template_name, context)
        # Create notice
        try:
            notice = Notice.objects.create(
                title=title,
                content=content,
                published=published,
                created_by=request.user,
            )

            messages.success(
                request, f'Notice "{notice.title}" has been created successfully.'
            )
            return redirect("dashboard:notice_list")

        except Exception as e:
            messages.error(request, f"Error creating notice: {str(e)}")
            context = self.get_context_data(**kwargs)
            context["form_data"] = request.POST
            return render(request, self.template_name, context)


class NoticeUpdateView(LoginRequiredMixin, TemplateView):
    """Notice edit page."""

    template_name = "dashboard/notices/edit.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_role_permission("can_update_notice"):
            messages.error(
                request, "Access denied. You don't have permission to update notices."
            )
            return redirect("dashboard:home")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["notice"] = get_object_or_404(Notice, pk=kwargs["pk"])
        return context

    def post(self, request, *args, **kwargs):
        """Handle notice update form submission."""
        notice = get_object_or_404(Notice, pk=kwargs["pk"])

        # Get form data
        title = request.POST.get("title", "").strip()
        content = request.POST.get("content", "").strip()
        published = request.POST.get("published") == "on"

        errors = {}

        # Validate required fields
        if not title:
            errors["title"] = "Title is required."

        if not content:
            errors["content"] = "Content is required."

        # If there are errors, return to form with errors
        if errors:
            context = self.get_context_data(**kwargs)
            context["errors"] = errors
            context["form_data"] = request.POST
            return render(request, self.template_name, context)
        # Update notice
        try:
            notice.title = title
            notice.content = content
            notice.published = published
            notice.save()

            messages.success(
                request, f'Notice "{notice.title}" has been updated successfully.'
            )
            return redirect("dashboard:notice_list")

        except Exception as e:
            messages.error(request, f"Error updating notice: {str(e)}")
            context = self.get_context_data(**kwargs)
            context["form_data"] = request.POST
            return render(request, self.template_name, context)


class NoticeDeleteView(LoginRequiredMixin, TemplateView):
    """Notice delete page."""

    template_name = "dashboard/notices/delete.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_role_permission("can_delete_notice"):
            messages.error(
                request, "Access denied. You don't have permission to delete notices."
            )
            return redirect("dashboard:home")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["notice"] = get_object_or_404(Notice, pk=kwargs["pk"])
        return context

    def post(self, request, *args, **kwargs):
        """Handle notice deletion."""
        notice = get_object_or_404(Notice, pk=kwargs["pk"])

        try:
            title = notice.title
            notice.delete()
            messages.success(
                request, f'Notice "{title}" has been deleted successfully.'
            )
        except Exception as e:
            messages.error(request, f"Error deleting notice: {str(e)}")

        return redirect("dashboard:notice_list")


class ApplicationDetailView(LoginRequiredMixin, TemplateView):
    """Application detail page."""

    template_name = "dashboard/applications/detail.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_role_permission("can_view_application"):
            messages.error(
                request,
                "Access denied. You don't have permission to view applications.",
            )
            return redirect("dashboard:home")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["application"] = get_object_or_404(
            AdmissionApplication, pk=kwargs["pk"]
        )
        return context


class ApplicationUpdateView(LoginRequiredMixin, TemplateView):
    """Application edit page."""

    template_name = "dashboard/applications/edit.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_role_permission("can_update_application"):
            messages.error(
                request,
                "Access denied. You don't have permission to update applications.",
            )
            return redirect("dashboard:home")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["application"] = get_object_or_404(
            AdmissionApplication, pk=kwargs["pk"]
        )
        context["status_choices"] = AdmissionApplication.STATUS_CHOICES
        return context

    def post(self, request, *args, **kwargs):
        """Handle application update form submission."""
        application = get_object_or_404(AdmissionApplication, pk=kwargs["pk"])

        # Get form data
        status = request.POST.get("status", "").strip()

        errors = {}

        # Validate status
        valid_statuses = [choice[0] for choice in AdmissionApplication.STATUS_CHOICES]
        if not status:
            errors["status"] = "Status is required."
        elif status not in valid_statuses:
            errors["status"] = "Invalid status selected."

        # If there are errors, return to form with errors
        if errors:
            context = self.get_context_data(**kwargs)
            context["errors"] = errors
            context["form_data"] = request.POST
            return render(request, self.template_name, context)

        # Update application
        try:
            application.status = status
            application.save()

            messages.success(
                request,
                f'Application for "{application.student_name}" has been updated successfully.',
            )
            return redirect("dashboard:application_list")

        except Exception as e:
            messages.error(request, f"Error updating application: {str(e)}")
            context = self.get_context_data(**kwargs)
            context["form_data"] = request.POST
            return render(request, self.template_name, context)


class ApplicationDeleteView(LoginRequiredMixin, TemplateView):
    """Application delete page."""

    template_name = "dashboard/applications/delete.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_role_permission("can_delete_application"):
            messages.error(
                request,
                "Access denied. You don't have permission to delete applications.",
            )
            return redirect("dashboard:home")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["application"] = get_object_or_404(
            AdmissionApplication, pk=kwargs["pk"]
        )
        return context

    def post(self, request, *args, **kwargs):
        """Handle application deletion."""
        application = get_object_or_404(AdmissionApplication, pk=kwargs["pk"])

        try:
            student_name = application.student_name
            application.delete()
            messages.success(
                request,
                f'Application for "{student_name}" has been deleted successfully.',
            )
        except Exception as e:
            messages.error(request, f"Error deleting application: {str(e)}")

        return redirect("dashboard:application_list")


class ApplicationExportView(LoginRequiredMixin, TemplateView):
    """Application export page."""

    template_name = "dashboard/applications/export.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_role_permission("can_export_data"):
            messages.error(
                request, "Access denied. You don't have permission to export data."
            )
            return redirect("dashboard:home")
        return super().dispatch(request, *args, **kwargs)


class UserCreateView(LoginRequiredMixin, TemplateView):
    """User creation page."""

    template_name = "dashboard/users/user_create.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_role_permission("can_add_user"):
            messages.error(
                request, "Access denied. You don't have permission to create users."
            )
            return redirect("dashboard:home")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["roles"] = Role.objects.all().order_by("name")
        return context

    def post(self, request, *args, **kwargs):
        """Handle user creation form submission."""
        # Get form data
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        phone_number = request.POST.get("phone_number", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        role_id = request.POST.get("role_id")
        password = request.POST.get("password", "").strip()
        password_confirm = request.POST.get("password_confirm", "").strip()

        errors = {}

        # Validate required fields
        if not username:
            errors["username"] = "Username is required."
        elif CustomUser.objects.filter(username=username).exists():
            errors["username"] = "A user with this username already exists."

        if not email:
            errors["email"] = "Email is required."
        elif CustomUser.objects.filter(email=email).exists():
            errors["email"] = "A user with this email already exists."

        if not phone_number:
            errors["phone_number"] = "Phone number is required."
        else:
            try:
                validate_bangladeshi_phone(phone_number)
            except ValidationError as e:
                errors["phone_number"] = str(e)

            if CustomUser.objects.filter(phone_number=phone_number).exists():
                errors["phone_number"] = "A user with this phone number already exists."

        # Validate role
        if not role_id:
            errors["role_id"] = "Role is required."
        else:
            try:
                role = Role.objects.get(pk=role_id)
            except Role.DoesNotExist:
                errors["role_id"] = "Invalid role selected."

        # Validate password
        if not password:
            errors["password"] = "Password is required."
        elif len(password) < 8:
            errors["password"] = "Password must be at least 8 characters long."
        elif password != password_confirm:
            errors["password_confirm"] = "Passwords do not match."

        # If there are errors, return to form with errors
        if errors:
            context = self.get_context_data(**kwargs)
            context["errors"] = errors
            context["form_data"] = request.POST
            return render(request, self.template_name, context)

        # Create user
        try:
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                phone_number=phone_number,
                first_name=first_name,
                last_name=last_name,
                role=role,
                password=password,
            )

            messages.success(
                request,
                f'User "{user.get_full_name() or user.username}" has been created successfully.',
            )
            return redirect("dashboard:user_list")

        except Exception as e:
            messages.error(request, f"Error creating user: {str(e)}")
            context = self.get_context_data(**kwargs)
            context["form_data"] = request.POST
            return render(request, self.template_name, context)


class UserUpdateView(LoginRequiredMixin, TemplateView):
    """User edit page."""

    template_name = "dashboard/users/user_edit.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_role_permission("can_update_user"):
            messages.error(
                request, "Access denied. You don't have permission to update users."
            )
            return redirect("dashboard:home")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_obj = get_object_or_404(CustomUser, pk=kwargs["pk"])
        context["user_obj"] = user_obj
        context["roles"] = Role.objects.all().order_by("name")
        return context

    def post(self, request, *args, **kwargs):
        """Handle user update form submission."""
        user_obj = get_object_or_404(CustomUser, pk=kwargs["pk"])

        # Get form data
        email = request.POST.get("email", "").strip()
        phone_number = request.POST.get("phone_number", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        role_id = request.POST.get("role_id")
        is_active = request.POST.get("is_active") == "on"
        password = request.POST.get("password", "").strip()
        password_confirm = request.POST.get("password_confirm", "").strip()

        errors = {}

        # Validate required fields
        if not email:
            errors["email"] = "Email is required."
        elif CustomUser.objects.filter(email=email).exclude(pk=user_obj.pk).exists():
            errors["email"] = "A user with this email already exists."

        if not phone_number:
            errors["phone_number"] = "Phone number is required."
        else:
            try:
                validate_bangladeshi_phone(phone_number)
            except ValidationError as e:
                errors["phone_number"] = str(e)

            if (
                CustomUser.objects.filter(phone_number=phone_number)
                .exclude(pk=user_obj.pk)
                .exists()
            ):
                errors["phone_number"] = "A user with this phone number already exists."

        # Validate role
        if not role_id:
            errors["role_id"] = "Role is required."
        else:
            try:
                role = Role.objects.get(pk=role_id)
            except Role.DoesNotExist:
                errors["role_id"] = "Invalid role selected."

        # Validate password if provided
        if password:
            if len(password) < 8:
                errors["password"] = "Password must be at least 8 characters long."
            elif password != password_confirm:
                errors["password_confirm"] = "Passwords do not match."

        # If there are errors, return to form with errors
        if errors:
            context = self.get_context_data(**kwargs)
            context["errors"] = errors
            context["form_data"] = request.POST
            return render(request, self.template_name, context)

        # Update user
        try:
            user_obj.email = email
            user_obj.phone_number = phone_number
            user_obj.first_name = first_name
            user_obj.last_name = last_name
            user_obj.role = role
            user_obj.is_active = is_active

            # Update password if provided
            if password:
                user_obj.set_password(password)

            user_obj.save()

            messages.success(
                request,
                f'User "{user_obj.get_full_name() or user_obj.username}" has been updated successfully.',
            )
            return redirect("dashboard:user_list")

        except Exception as e:
            messages.error(request, f"Error updating user: {str(e)}")
            context = self.get_context_data(**kwargs)
            context["form_data"] = request.POST
            return render(request, self.template_name, context)


class UserDeleteView(LoginRequiredMixin, TemplateView):
    """User delete page."""

    template_name = "dashboard/users/user_delete.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_role_permission("can_delete_user"):
            messages.error(
                request, "Access denied. You don't have permission to delete users."
            )
            return redirect("dashboard:home")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_obj = get_object_or_404(CustomUser, pk=kwargs["pk"])
        context["user_obj"] = user_obj
        context["is_self"] = user_obj.pk == self.request.user.pk
        return context

    def post(self, request, *args, **kwargs):
        """Handle user deletion."""
        user_obj = get_object_or_404(CustomUser, pk=kwargs["pk"])

        # Prevent self-deletion
        if user_obj.pk == request.user.pk:
            messages.error(request, "You cannot delete your own account.")
            return redirect("dashboard:user_list")

        try:
            username = user_obj.get_full_name() or user_obj.username
            user_obj.delete()
            messages.success(
                request, f'User "{username}" has been deleted successfully.'
            )
        except Exception as e:
            messages.error(request, f"Error deleting user: {str(e)}")

        return redirect("dashboard:user_list")


# API ViewSets
class NoticeViewSet(ModelViewSet):
    """ViewSet for notice management."""

    serializer_class = NoticeManagementSerializer
    permission_classes = [IsAuthenticated, NoticeManagementPermission]
    pagination_class = DashboardPagination

    def get_queryset(self):
        """Get notices with optional filtering."""
        queryset = Notice.objects.select_related("created_by").all()

        # Search functionality
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(content__icontains=search)
            )

        # Filter by published status
        published = self.request.query_params.get("published")
        if published == "true":
            queryset = queryset.filter(published=True)
        elif published == "false":
            queryset = queryset.filter(published=False)

        return queryset.order_by("-date_created")

    def update(self, request, *args, **kwargs):
        """Update a notice with permission check."""
        notice = self.get_object()
        if not notice.can_be_edited_by(request.user):
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete a notice with permission check."""
        notice = self.get_object()
        if not notice.can_be_deleted_by(request.user):
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        notice.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["post"])
    def bulk_action(self, request):
        """Perform bulk actions on notices."""
        serializer = BulkActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        notice_ids = serializer.validated_data["ids"]
        action_type = serializer.validated_data["action"]
        notices = Notice.objects.filter(id__in=notice_ids)

        if action_type == "publish":
            notices.update(published=True)
        elif action_type == "unpublish":
            notices.update(published=False)
        elif action_type == "delete":
            notices.delete()

        return Response({"message": f"Bulk {action_type} completed successfully"})


class AdmissionApplicationViewSet(ModelViewSet):
    """ViewSet for admission application management."""

    serializer_class = AdmissionApplicationManagementSerializer
    permission_classes = [IsAuthenticated, ApplicationManagementPermission]
    pagination_class = DashboardPagination

    def get_queryset(self):
        """Get applications with optional filtering."""
        queryset = AdmissionApplication.objects.all()

        # Search functionality
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(student_name__icontains=search)
                | Q(guardian_name__icontains=search)
                | Q(enrolled_class__icontains=search)
            )

        # Filter by status
        status_filter = self.request.query_params.get("status")
        if status_filter and status_filter != "all":
            queryset = queryset.filter(status=status_filter)

        return queryset.order_by("-date_submitted")

    def update(self, request, *args, **kwargs):
        """Update an application with permission check."""
        application = self.get_object()
        if not application.can_be_updated_by(request.user):
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete an application with permission check."""
        application = self.get_object()
        if not application.can_be_deleted_by(request.user):
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        application.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"])
    def export_csv(self, request):
        """Export applications to CSV."""
        applications = self.get_queryset()

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="applications.csv"'

        writer = csv.writer(response)
        writer.writerow(
            [
                "Student Name",
                "Date of Birth",
                "Class",
                "Guardian Name",
                "Guardian Mobile",
                "Guardian Email",
                "Status",
                "Date Submitted",
            ]
        )

        for app in applications:
            writer.writerow(
                [
                    app.student_name,
                    app.student_dob,
                    app.enrolled_class,
                    app.guardian_name,
                    app.guardian_mobile,
                    app.guardian_email,
                    app.status,
                    app.date_submitted.strftime("%Y-%m-%d"),
                ]
            )

        return response

    @action(detail=False, methods=["post"])
    def bulk_action(self, request):
        """Perform bulk actions on applications."""
        serializer = BulkActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        app_ids = serializer.validated_data["ids"]
        action_type = serializer.validated_data["action"]
        applications = AdmissionApplication.objects.filter(id__in=app_ids)

        if action_type == "accept":
            applications.update(status="accepted")
        elif action_type == "reject":
            applications.update(status="rejected")
        elif action_type == "pending":
            applications.update(status="pending")
        elif action_type == "delete":
            applications.delete()

        return Response({"message": f"Bulk {action_type} completed successfully"})


class UserViewSet(ModelViewSet):
    """ViewSet for user management (SuperAdmin only)."""

    serializer_class = UserManagementSerializer
    permission_classes = [IsAuthenticated, IsSuperAdminPermission]
    pagination_class = DashboardPagination

    def get_queryset(self):
        """Get users with optional filtering."""
        queryset = CustomUser.objects.select_related("role").all()

        # Search functionality
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search)
                | Q(email__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
            )

        return queryset.order_by("-date_joined")

    def update(self, request, *args, **kwargs):
        """Update user with proper permission checks."""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        # Check if user is trying to modify their own account
        if instance.pk == request.user.pk:
            # Allow self-modification but with restrictions
            serializer = self.get_serializer(
                instance, data=request.data, partial=partial
            )
            serializer.is_valid(raise_exception=True)

            # Don't allow changing own role to lower privilege
            if "role" in serializer.validated_data:
                new_role = serializer.validated_data["role"]
                if not request.user.is_super_admin() or (
                    new_role and new_role.name not in ["SuperAdmin", "Admin"]
                ):
                    return Response(
                        {"error": "Cannot change your own role to lower privilege"},
                        status=status.HTTP_403_FORBIDDEN,
                    )

            self.perform_update(serializer)
            return Response(serializer.data)

        # For other users, proceed normally
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete user with permission check."""
        instance = self.get_object()

        # Prevent self-deletion
        if instance.pk == request.user.pk:
            return Response(
                {"error": "Cannot delete your own account"},
                status=status.HTTP_403_FORBIDDEN,
            )

        return super().destroy(request, *args, **kwargs)


class RoleViewSet(ModelViewSet):
    """ViewSet for role management (SuperAdmin only)."""

    serializer_class = RoleManagementSerializer
    permission_classes = [IsAuthenticated, IsSuperAdminPermission]
    pagination_class = DashboardPagination

    def get_queryset(self):
        """Get roles with optional filtering."""
        queryset = Role.objects.all()

        # Search functionality
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )

        return queryset.order_by("name")

    def destroy(self, request, *args, **kwargs):
        """Delete role with protection for system roles and roles with users."""
        role = self.get_object()

        # Protect system roles
        system_roles = ["SuperAdmin", "Admin", "Teacher", "Guest"]
        if role.name in system_roles:
            return Response(
                {"error": f"Cannot delete system role '{role.name}'"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check if role has users
        user_count = role.customuser_set.count()
        if user_count > 0:
            return Response(
                {
                    "error": f"Cannot delete role '{role.name}' because it has {user_count} user(s) assigned to it"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        role.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get"])
    def users(self, request, pk=None):
        """Get users assigned to this role."""
        role = self.get_object()
        users = role.customuser_set.select_related("role").all()

        # Apply pagination
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(users, request)

        user_data = [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.get_full_name() or user.username,
                "is_active": user.is_active,
                "date_joined": user.date_joined.isoformat(),
            }
            for user in page
        ]

        return paginator.get_paginated_response(user_data)


class UserProfileAPIView(APIView):
    """API view for user profile management."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get current user profile."""
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        """Update current user profile."""
        serializer = UserProfileSerializer(
            request.user, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Profile updated successfully"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Search functionality
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(content__icontains=search)
            )

        # Filter by published status
        published = self.request.query_params.get("published")
        if published == "true":
            queryset = queryset.filter(published=True)
        elif published == "false":
            queryset = queryset.filter(published=False)

        return queryset.order_by("-date_created")

    def update(self, request, *args, **kwargs):
        """Update a notice with permission check."""
        notice = self.get_object()
        if not notice.can_be_edited_by(request.user):
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete a notice with permission check."""
        notice = self.get_object()
        if not notice.can_be_deleted_by(request.user):
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        notice.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["post"])
    def bulk_action(self, request):
        """Perform bulk actions on notices."""
        serializer = BulkActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        notice_ids = serializer.validated_data["ids"]
        action_type = serializer.validated_data["action"]
        notices = Notice.objects.filter(id__in=notice_ids)

        if action_type == "publish":
            notices.update(published=True)
        elif action_type == "unpublish":
            notices.update(published=False)
        elif action_type == "delete":
            notices.delete()

        return Response({"message": f"Bulk {action_type} completed successfully"})


class AdmissionApplicationViewSet(ModelViewSet):
    """ViewSet for admission application management."""

    serializer_class = AdmissionApplicationManagementSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdminPermission]
    pagination_class = DashboardPagination
    http_method_names = ["get", "patch", "delete", "post"]

    def get_queryset(self):
        """Get applications with optional filtering."""
        queryset = AdmissionApplication.objects.all()

        # Search functionality
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(student_name__icontains=search)
                | Q(guardian_name__icontains=search)
                | Q(enrolled_class__icontains=search)
            )

        # Filter by status
        status_filter = self.request.query_params.get("status")
        if status_filter and status_filter != "all":
            queryset = queryset.filter(status=status_filter)

        return queryset.order_by("-date_submitted")

    def update(self, request, *args, **kwargs):
        """Update an application with permission check."""
        application = self.get_object()
        if not application.can_be_updated_by(request.user):
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete an application with permission check."""
        application = self.get_object()
        if not application.can_be_deleted_by(request.user):
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        application.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"])
    def export_csv(self, request):
        """Export applications to CSV."""
        applications = self.get_queryset()

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="applications.csv"'

        writer = csv.writer(response)
        writer.writerow(
            [
                "Student Name",
                "Date of Birth",
                "Class",
                "Guardian Name",
                "Guardian Mobile",
                "Guardian Email",
                "Status",
                "Date Submitted",
            ]
        )

        for app in applications:
            writer.writerow(
                [
                    app.student_name,
                    app.student_dob,
                    app.enrolled_class,
                    app.guardian_name,
                    app.guardian_mobile,
                    app.guardian_email,
                    app.status,
                    app.date_submitted.strftime("%Y-%m-%d"),
                ]
            )

        return response

    @action(detail=False, methods=["post"])
    def bulk_action(self, request):
        """Perform bulk actions on applications."""
        serializer = BulkActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        app_ids = serializer.validated_data["ids"]
        action_type = serializer.validated_data["action"]
        applications = AdmissionApplication.objects.filter(id__in=app_ids)

        if action_type == "accept":
            applications.update(status="accepted")
        elif action_type == "reject":
            applications.update(status="rejected")
        elif action_type == "pending":
            applications.update(status="pending")
        elif action_type == "delete":
            applications.delete()

        return Response({"message": f"Bulk {action_type} completed successfully"})


class UserViewSet(ModelViewSet):
    """ViewSet for user management (SuperAdmin only)."""

    serializer_class = UserManagementSerializer
    permission_classes = [IsAuthenticated, IsSuperAdminPermission]
    pagination_class = DashboardPagination

    def get_queryset(self):
        """Get users with optional filtering."""
        queryset = CustomUser.objects.select_related("role").all()

        # Search functionality
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search)
                | Q(email__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
            )

        return queryset.order_by("-date_joined")

    def update(self, request, *args, **kwargs):
        """Update user with proper permission checks."""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        # Check if user is trying to modify their own account
        if instance.pk == request.user.pk:
            # Allow self-modification but with restrictions
            serializer = self.get_serializer(
                instance, data=request.data, partial=partial
            )
            serializer.is_valid(raise_exception=True)

            # Don't allow changing own role to lower privilege
            if "role" in serializer.validated_data:
                new_role = serializer.validated_data["role"]
                if not request.user.is_super_admin() or (
                    new_role and new_role.name not in ["SuperAdmin", "Admin"]
                ):
                    return Response(
                        {"error": "Cannot change your own role to lower privilege"},
                        status=status.HTTP_403_FORBIDDEN,
                    )

            self.perform_update(serializer)
            return Response(serializer.data)

        # For other users, proceed normally
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete user with permission check."""
        instance = self.get_object()

        # Prevent self-deletion
        if instance.pk == request.user.pk:
            return Response(
                {"error": "Cannot delete your own account"},
                status=status.HTTP_403_FORBIDDEN,
            )

        return super().destroy(request, *args, **kwargs)


class RoleViewSet(ModelViewSet):
    """ViewSet for role management (SuperAdmin only)."""

    serializer_class = RoleManagementSerializer
    permission_classes = [IsAuthenticated, IsSuperAdminPermission]
    pagination_class = DashboardPagination

    def get_queryset(self):
        """Get roles with optional filtering."""
        queryset = Role.objects.all()

        # Search functionality
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )

        return queryset.order_by("name")

    def destroy(self, request, *args, **kwargs):
        """Delete role with protection for system roles and roles with users."""
        role = self.get_object()

        # Protect system roles
        system_roles = ["SuperAdmin", "Admin", "Teacher", "Guest"]
        if role.name in system_roles:
            return Response(
                {"error": f"Cannot delete system role '{role.name}'"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check if role has users
        user_count = role.customuser_set.count()
        if user_count > 0:
            return Response(
                {
                    "error": f"Cannot delete role '{role.name}' because it has {user_count} user(s) assigned to it"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        role.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get"])
    def users(self, request, pk=None):
        """Get users assigned to this role."""
        role = self.get_object()
        users = role.customuser_set.select_related("role").all()

        # Apply pagination
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(users, request)

        user_data = [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.get_full_name() or user.username,
                "is_active": user.is_active,
                "date_joined": user.date_joined.isoformat(),
            }
            for user in page
        ]

        return paginator.get_paginated_response(user_data)


class UserProfileAPIView(APIView):
    """API view for user profile management."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get current user profile."""
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        """Update current user profile."""
        serializer = UserProfileSerializer(
            request.user, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Profile updated successfully"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
