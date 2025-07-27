from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Q
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.paginator import Paginator
from accounts.models import Role


class RoleListView(LoginRequiredMixin, TemplateView):
    """Role management page."""

    template_name = "dashboard/roles/role_list.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_role_permission("can_view_role"):
            messages.error(
                request, "Access denied. You don't have permission to view roles."
            )
            return redirect("dashboard:home")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        roles = Role.objects.all()

        # Get search and filter parameters
        search_query = self.request.GET.get("search", "").strip()
        ordering = self.request.GET.get("ordering", "name")

        # Apply search filter
        if search_query:
            roles = roles.filter(
                Q(name__icontains=search_query) | Q(description__icontains=search_query)
            )

        # Apply ordering
        valid_orderings = [
            "name",
            "-name",
            "created_at",
            "-created_at",
            "updated_at",
            "-updated_at",
        ]
        if ordering in valid_orderings:
            roles = roles.order_by(ordering)
        else:
            roles = roles.order_by("name")

        # Add user count annotation
        roles = roles.annotate(user_count=Count("customuser"))

        # Pagination
        paginator = Paginator(roles, 10)
        page = self.request.GET.get("page")
        context["roles"] = paginator.get_page(page)

        # Add search context for form persistence
        context["search_query"] = search_query
        context["ordering"] = ordering

        return context


class RoleCreateView(LoginRequiredMixin, TemplateView):
    """Role creation page."""

    template_name = "dashboard/roles/role_create.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_role_permission("can_add_role"):
            messages.error(
                request, "Access denied. You don't have permission to create roles."
            )
            return redirect("dashboard:home")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Define available permissions with granular control
        context["available_permissions"] = {
            "can_view_dashboard": "Can view dashboard",
            # Notice permissions
            "can_view_notice": "Can view notices",
            "can_add_notice": "Can add notices",
            "can_update_notice": "Can update notices",
            "can_delete_notice": "Can delete notices",
            # Application permissions
            "can_view_application": "Can view applications",
            "can_add_application": "Can add applications",
            "can_update_application": "Can update applications",
            "can_delete_application": "Can delete applications",
            # User permissions
            "can_view_user": "Can view users",
            "can_add_user": "Can add users",
            "can_update_user": "Can update users",
            "can_delete_user": "Can delete users",
            # Role permissions
            "can_view_role": "Can view roles",
            "can_add_role": "Can add roles",
            "can_update_role": "Can update roles",
            "can_delete_role": "Can delete roles",
            # Other permissions
            "can_export_data": "Can export data",
            "can_view_reports": "Can view reports",
            "can_moderate_content": "Can moderate content",
            "can_access_settings": "Can access settings",
        }
        return context

    def post(self, request, *args, **kwargs):
        """Handle role creation form submission."""
        # Get form data
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()

        # Get permissions
        permissions = {}
        available_permissions = [
            "can_view_dashboard",
            # Notice permissions
            "can_view_notice",
            "can_add_notice",
            "can_update_notice",
            "can_delete_notice",
            # Application permissions
            "can_view_application",
            "can_add_application",
            "can_update_application",
            "can_delete_application",
            # User permissions
            "can_view_user",
            "can_add_user",
            "can_update_user",
            "can_delete_user",
            # Role permissions
            "can_view_role",
            "can_add_role",
            "can_update_role",
            "can_delete_role",
            # Other permissions
            "can_export_data",
            "can_view_reports",
            "can_moderate_content",
            "can_access_settings",
        ]

        for perm in available_permissions:
            permissions[perm] = request.POST.get(perm) == "on"

        errors = {}

        # Validate required fields
        if not name:
            errors["name"] = "Role name is required."
        elif Role.objects.filter(name=name).exists():
            errors["name"] = "A role with this name already exists."

        # If there are errors, return to form with errors
        if errors:
            context = self.get_context_data(**kwargs)
            context["errors"] = errors
            context["form_data"] = request.POST
            return render(request, self.template_name, context)

        # Create role
        try:
            role = Role.objects.create(
                name=name,
                description=description,
                permissions=permissions,
            )

            messages.success(
                request, f'Role "{role.name}" has been created successfully.'
            )
            return redirect("dashboard:role_list")

        except Exception as e:
            messages.error(request, f"Error creating role: {str(e)}")
            context = self.get_context_data(**kwargs)
            context["form_data"] = request.POST
            return render(request, self.template_name, context)


class RoleUpdateView(LoginRequiredMixin, TemplateView):
    """Role edit page."""

    template_name = "dashboard/roles/role_edit.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_role_permission("can_update_role"):
            messages.error(
                request, "Access denied. You don't have permission to update roles."
            )
            return redirect("dashboard:home")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["role"] = get_object_or_404(Role, pk=kwargs["pk"])
        # Define available permissions with granular control
        context["available_permissions"] = {
            "can_view_dashboard": "Can view dashboard",
            # Notice permissions
            "can_view_notice": "Can view notices",
            "can_add_notice": "Can add notices",
            "can_update_notice": "Can update notices",
            "can_delete_notice": "Can delete notices",
            # Application permissions
            "can_view_application": "Can view applications",
            "can_add_application": "Can add applications",
            "can_update_application": "Can update applications",
            "can_delete_application": "Can delete applications",
            # User permissions
            "can_view_user": "Can view users",
            "can_add_user": "Can add users",
            "can_update_user": "Can update users",
            "can_delete_user": "Can delete users",
            # Role permissions
            "can_view_role": "Can view roles",
            "can_add_role": "Can add roles",
            "can_update_role": "Can update roles",
            "can_delete_role": "Can delete roles",
            # Other permissions
            "can_export_data": "Can export data",
            "can_view_reports": "Can view reports",
            "can_moderate_content": "Can moderate content",
            "can_access_settings": "Can access settings",
        }
        return context

    def post(self, request, *args, **kwargs):
        """Handle role update form submission."""
        role = get_object_or_404(Role, pk=kwargs["pk"])

        # Get form data
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()

        # Get permissions
        permissions = {}
        available_permissions = [
            "can_view_dashboard",
            # Notice permissions
            "can_view_notice",
            "can_add_notice",
            "can_update_notice",
            "can_delete_notice",
            # Application permissions
            "can_view_application",
            "can_add_application",
            "can_update_application",
            "can_delete_application",
            # User permissions
            "can_view_user",
            "can_add_user",
            "can_update_user",
            "can_delete_user",
            # Role permissions
            "can_view_role",
            "can_add_role",
            "can_update_role",
            "can_delete_role",
            # Other permissions
            "can_export_data",
            "can_view_reports",
            "can_moderate_content",
            "can_access_settings",
        ]

        for perm in available_permissions:
            permissions[perm] = request.POST.get(perm) == "on"

        errors = {}

        # Validate required fields
        if not name:
            errors["name"] = "Role name is required."
        elif Role.objects.filter(name=name).exclude(pk=role.pk).exists():
            errors["name"] = "A role with this name already exists."

        # If there are errors, return to form with errors
        if errors:
            context = self.get_context_data(**kwargs)
            context["errors"] = errors
            context["form_data"] = request.POST
            return render(request, self.template_name, context)

        # Update role
        try:
            role.name = name
            role.description = description
            role.permissions = permissions
            role.save()

            messages.success(
                request, f'Role "{role.name}" has been updated successfully.'
            )
            return redirect("dashboard:role_list")

        except Exception as e:
            messages.error(request, f"Error updating role: {str(e)}")
            context = self.get_context_data(**kwargs)
            context["form_data"] = request.POST
            return render(request, self.template_name, context)


class RoleDeleteView(LoginRequiredMixin, TemplateView):
    """Role delete page."""

    template_name = "dashboard/roles/role_delete.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_role_permission("can_delete_role"):
            messages.error(
                request, "Access denied. You don't have permission to delete roles."
            )
            return redirect("dashboard:home")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        role = get_object_or_404(Role, pk=kwargs["pk"])
        context["role"] = role
        context["user_count"] = role.customuser_set.count()
        context["is_system_role"] = role.name in [
            "SuperAdmin",
            "Admin",
            "Teacher",
            "Guest",
        ]
        return context

    def post(self, request, *args, **kwargs):
        """Handle role deletion."""
        role = get_object_or_404(Role, pk=kwargs["pk"])

        # Check if it's a system role
        system_roles = ["SuperAdmin", "Admin", "Teacher", "Guest"]
        if role.name in system_roles:
            messages.error(request, f"Cannot delete system role '{role.name}'.")
            return redirect("dashboard:role_list")

        # Check if role has users
        user_count = role.customuser_set.count()
        if user_count > 0:
            messages.error(
                request,
                f"Cannot delete role '{role.name}' because it has {user_count} user(s) assigned to it.",
            )
            return redirect("dashboard:role_list")

        try:
            name = role.name
            role.delete()
            messages.success(request, f'Role "{name}" has been deleted successfully.')
        except Exception as e:
            messages.error(request, f"Error deleting role: {str(e)}")

        return redirect("dashboard:role_list")


class RoleDetailView(LoginRequiredMixin, TemplateView):
    """Role detail page."""

    template_name = "dashboard/roles/role_detail.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_role_permission("can_view_role"):
            messages.error(
                request, "Access denied. You don't have permission to view roles."
            )
            return redirect("dashboard:home")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        role = get_object_or_404(Role, pk=kwargs["pk"])
        context["role"] = role

        # Get users with this role
        users = role.customuser_set.select_related("role").all()
        paginator = Paginator(users, 10)
        page = self.request.GET.get("page")
        context["users"] = paginator.get_page(page)

        context["user_count"] = role.customuser_set.count()
        context["is_system_role"] = role.name in [
            "SuperAdmin",
            "Admin",
            "Teacher",
            "Guest",
        ]

        return context
