from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission


class Command(BaseCommand):

    help = "Create default user groups and permissions"


    def handle(self, *args, **kwargs):

        groups_permissions = {

            "ADMIN": [
                "all",
            ],

            "AIRLINE_OPERATOR": [
                "view_flight",
                "change_flight",
                "view_gateassignment",
            ],

            "AIRPORT_MANAGER": [
                "view_flight",
                "add_flight",
                "change_flight",
                "view_gateassignment",
                "add_groundoperation",
                "change_groundoperation",
                "view_securityreport",
            ],

            "GROUND_STAFF": [
                "view_groundoperation",
                "add_groundoperation",
                "change_groundoperation",
            ],

            "SECURITY_OFFICER": [
                "view_securityreport",
                "add_securityreport",
                "change_securityreport",
            ],

            "PASSENGER_SERVICE": [
                "view_notification",
            ],
        }


        for group_name, permissions in groups_permissions.items():

            group, _ = Group.objects.get_or_create(
                name=group_name
            )

            if "all" in permissions:
                all_permissions = Permission.objects.all()
                group.permissions.set(all_permissions)

            else:
                perms = Permission.objects.filter(
                    codename__in=permissions
                )

                group.permissions.set(perms)

            group.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f"{group_name} permissions updated"
                )
            )