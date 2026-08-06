from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from airlines.models import Airline
from airports.models import Airport, Gate, Terminal
from audit.models import AuditLog
from fleet.models import Aircraft, AircraftType
from flights.models import Flight, GateAssignment
from notifications.models import Notification
from operations.models import GroundOperation, OperationType
from passenger_service.models import PassengerRequest
from security.models import SecurityReport


User = get_user_model()


class Command(BaseCommand):
    help = (
        "Create deterministic, connected demo data "
        "for the Airport Management System."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            required=True,
            help="Password assigned to all demo users.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        password = options["password"]
        now = timezone.now().replace(
            second=0,
            microsecond=0,
        )

        self.stdout.write(
            self.style.MIGRATE_HEADING(
                "Creating Airport Management demo data..."
            )
        )

        airports = self.create_airports()
        gates = self.create_terminals_and_gates(
            airports
        )
        airlines = self.create_airlines()
        aircraft = self.create_fleet(airlines)
        users = self.create_users(
            airlines,
            password,
        )
        operation_types = (
            self.create_operation_types()
        )
        flights = self.create_flights(
            now,
            airports,
            airlines,
            aircraft,
        )

        self.create_gate_assignments(
            now,
            flights,
            gates,
        )
        self.create_ground_operations(
            now,
            flights,
            users,
            operation_types,
        )
        self.create_security_reports(
            flights,
            users,
        )
        self.create_passenger_requests(
            flights,
            users,
        )
        self.create_notifications(
            flights,
            users,
        )
        self.create_audit_logs(
            flights,
            users,
        )

        self.print_summary(password)

    def create_airports(self):
        airport_data = [
            {
                "iata_code": "IKA",
                "name": (
                    "Imam Khomeini "
                    "International Airport"
                ),
                "icao_code": "OIIE",
                "country": "Iran",
                "city": "Tehran",
                "address": "Tehran Province, Iran",
            },
            {
                "iata_code": "MHD",
                "name": (
                    "Mashhad Shahid Hasheminejad "
                    "International Airport"
                ),
                "icao_code": "OIMM",
                "country": "Iran",
                "city": "Mashhad",
                "address": "Mashhad, Iran",
            },
            {
                "iata_code": "SYZ",
                "name": (
                    "Shiraz Shahid Dastgheib "
                    "International Airport"
                ),
                "icao_code": "OISS",
                "country": "Iran",
                "city": "Shiraz",
                "address": "Shiraz, Iran",
            },
            {
                "iata_code": "TBZ",
                "name": (
                    "Tabriz Shahid Madani "
                    "International Airport"
                ),
                "icao_code": "OITT",
                "country": "Iran",
                "city": "Tabriz",
                "address": "Tabriz, Iran",
            },
        ]

        airports = {}

        for data in airport_data:
            airport, _ = (
                Airport.objects.update_or_create(
                    iata_code=data["iata_code"],
                    defaults=data,
                )
            )

            airports[data["iata_code"]] = airport

        self.stdout.write(
            self.style.SUCCESS(
                f"Airports: {len(airports)}"
            )
        )

        return airports

    def create_terminals_and_gates(
        self,
        airports,
    ):
        terminal_data = [
            ("IKA-T1", "IKA", "Terminal 1"),
            ("IKA-T2", "IKA", "Terminal 2"),
            ("MHD-T1", "MHD", "Terminal 1"),
            ("MHD-T2", "MHD", "Terminal 2"),
            ("SYZ-T1", "SYZ", "Main Terminal"),
            ("TBZ-T1", "TBZ", "Main Terminal"),
        ]

        terminals = {}

        for code, airport_code, name in terminal_data:
            terminal, _ = (
                Terminal.objects.update_or_create(
                    code=code,
                    defaults={
                        "airport": airports[
                            airport_code
                        ],
                        "name": name,
                        "description": (
                            "Demo operational terminal."
                        ),
                    },
                )
            )

            terminals[code] = terminal

        gate_data = [
            ("IKA-A01", "IKA-T1", "Gate A01"),
            ("IKA-A02", "IKA-T1", "Gate A02"),
            ("IKA-A03", "IKA-T1", "Gate A03"),
            ("IKA-B01", "IKA-T2", "Gate B01"),
            ("MHD-A01", "MHD-T1", "Gate A01"),
            ("MHD-A02", "MHD-T1", "Gate A02"),
            ("MHD-B01", "MHD-T2", "Gate B01"),
            ("SYZ-A01", "SYZ-T1", "Gate A01"),
            ("SYZ-A02", "SYZ-T1", "Gate A02"),
            ("TBZ-A01", "TBZ-T1", "Gate A01"),
            ("TBZ-A02", "TBZ-T1", "Gate A02"),
            ("TBZ-A03", "TBZ-T1", "Gate A03"),
        ]

        gates = {}

        for code, terminal_code, name in gate_data:
            gate, _ = Gate.objects.update_or_create(
                code=code,
                defaults={
                    "terminal": terminals[
                        terminal_code
                    ],
                    "name": name,
                    "is_active": True,
                },
            )

            gates[code] = gate

        self.stdout.write(
            self.style.SUCCESS(
                f"Terminals: {len(terminals)} | "
                f"Gates: {len(gates)}"
            )
        )

        return gates

    def create_airlines(self):
        airline_data = [
            {
                "iata_code": "IR",
                "name": "Iran Air",
                "icao_code": "IRA",
                "country": "Iran",
                "website": "https://iranair.com",
                "contact_email": (
                    "operations@demo-iranair.local"
                ),
                "is_active": True,
            },
            {
                "iata_code": "W5",
                "name": "Mahan Air",
                "icao_code": "IRM",
                "country": "Iran",
                "website": "https://mahan.aero",
                "contact_email": (
                    "operations@demo-mahan.local"
                ),
                "is_active": True,
            },
            {
                "iata_code": "EP",
                "name": "Iran Aseman Airlines",
                "icao_code": "IRC",
                "country": "Iran",
                "website": None,
                "contact_email": (
                    "operations@demo-aseman.local"
                ),
                "is_active": True,
            },
        ]

        airlines = {}

        for data in airline_data:
            airline, _ = (
                Airline.objects.update_or_create(
                    iata_code=data["iata_code"],
                    defaults=data,
                )
            )

            airlines[
                data["iata_code"]
            ] = airline

        self.stdout.write(
            self.style.SUCCESS(
                f"Airlines: {len(airlines)}"
            )
        )

        return airlines

    def create_fleet(self, airlines):
        type_data = [
            (
                "Airbus",
                "A320-200",
                180,
                6100,
            ),
            (
                "Airbus",
                "A321-200",
                220,
                5950,
            ),
            (
                "Boeing",
                "737-800",
                189,
                5765,
            ),
            (
                "ATR",
                "72-600",
                72,
                1528,
            ),
        ]

        aircraft_types = {}

        for (
            manufacturer,
            model,
            capacity,
            range_km,
        ) in type_data:
            aircraft_type, _ = (
                AircraftType.objects
                .update_or_create(
                    manufacturer=manufacturer,
                    model=model,
                    defaults={
                        "passenger_capacity": (
                            capacity
                        ),
                        "range_km": range_km,
                        "is_active": True,
                    },
                )
            )

            aircraft_types[
                f"{manufacturer}-{model}"
            ] = aircraft_type

        aircraft_data = [
            (
                "EP-IRA",
                "IR",
                "Airbus-A320-200",
                "IR-A320-001",
                2015,
            ),
            (
                "EP-IRB",
                "IR",
                "Airbus-A321-200",
                "IR-A321-002",
                2017,
            ),
            (
                "EP-MHA",
                "W5",
                "Airbus-A320-200",
                "W5-A320-001",
                2016,
            ),
            (
                "EP-MHB",
                "W5",
                "Boeing-737-800",
                "W5-B738-002",
                2018,
            ),
            (
                "EP-ASA",
                "EP",
                "ATR-72-600",
                "EP-ATR-001",
                2019,
            ),
            (
                "EP-ASB",
                "EP",
                "Boeing-737-800",
                "EP-B738-002",
                2014,
            ),
        ]

        aircraft = {}

        for (
            registration,
            airline_code,
            type_key,
            serial,
            year,
        ) in aircraft_data:
            item, _ = (
                Aircraft.objects.update_or_create(
                    registration_number=(
                        registration
                    ),
                    defaults={
                        "airline": airlines[
                            airline_code
                        ],
                        "aircraft_type": (
                            aircraft_types[
                                type_key
                            ]
                        ),
                        "serial_number": serial,
                        "manufacture_year": year,
                        "status": "ACTIVE",
                    },
                )
            )

            aircraft[registration] = item

        self.stdout.write(
            self.style.SUCCESS(
                f"Aircraft types: "
                f"{len(aircraft_types)} | "
                f"Aircraft: {len(aircraft)}"
            )
        )

        return aircraft

    def create_users(
        self,
        airlines,
        password,
    ):
        user_data = [
            {
                "username": "demo_admin",
                "role": "ADMIN",
                "email": "admin@airport-demo.local",
                "first_name": "Airport",
                "last_name": "Administrator",
                "is_staff": True,
                "is_superuser": True,
                "airline": None,
            },
            {
                "username": "demo_manager",
                "role": "AIRPORT_MANAGER",
                "email": "manager@airport-demo.local",
                "first_name": "Sara",
                "last_name": "Ahmadi",
                "airline": None,
            },
            {
                "username": "demo_ground",
                "role": "GROUND_STAFF",
                "email": "ground@airport-demo.local",
                "first_name": "Reza",
                "last_name": "Karimi",
                "airline": None,
            },
            {
                "username": "demo_security",
                "role": "SECURITY_OFFICER",
                "email": "security@airport-demo.local",
                "first_name": "Arman",
                "last_name": "Hosseini",
                "airline": None,
            },
            {
                "username": "demo_passenger",
                "role": "PASSENGER_SERVICE",
                "email": "passenger@airport-demo.local",
                "first_name": "Niloofar",
                "last_name": "Moradi",
                "airline": None,
            },
            {
                "username": "demo_iran_operator",
                "role": "AIRLINE_OPERATOR",
                "email": "iran@airport-demo.local",
                "first_name": "Amir",
                "last_name": "Rahimi",
                "airline": airlines["IR"],
            },
            {
                "username": "demo_mahan_operator",
                "role": "AIRLINE_OPERATOR",
                "email": "mahan@airport-demo.local",
                "first_name": "Mina",
                "last_name": "Jafari",
                "airline": airlines["W5"],
            },
        ]

        users = {}

        for data in user_data:
            username = data["username"]

            defaults = {
                **data,
                "is_active": True,
            }

            defaults.pop("username")

            user, _ = User.objects.update_or_create(
                username=username,
                defaults=defaults,
            )

            user.set_password(password)
            user.save(
                update_fields=["password"]
            )

            users[username] = user

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo users: {len(users)}"
            )
        )

        return users

    def create_operation_types(self):
        data = [
            (
                "Refueling",
                "Aircraft fuel service.",
            ),
            (
                "Baggage Handling",
                "Loading and unloading baggage.",
            ),
            (
                "Cabin Cleaning",
                "Cabin turnaround cleaning.",
            ),
            (
                "Catering",
                "Aircraft catering service.",
            ),
            (
                "Pushback",
                "Aircraft pushback preparation.",
            ),
            (
                "Technical Inspection",
                "Pre-departure technical check.",
            ),
        ]

        operation_types = {}

        for name, description in data:
            item, _ = (
                OperationType.objects
                .update_or_create(
                    name=name,
                    defaults={
                        "description": description,
                        "is_active": True,
                    },
                )
            )

            operation_types[name] = item

        return operation_types

    def create_flights(
        self,
        now,
        airports,
        airlines,
        aircraft,
    ):
        flight_data = [
            {
                "number": "IR720",
                "airline": "IR",
                "aircraft": "EP-IRA",
                "origin": "IKA",
                "destination": "MHD",
                "departure": -6,
                "duration": 1.5,
                "status": "ARRIVED",
            },
            {
                "number": "W5102",
                "airline": "W5",
                "aircraft": "EP-MHA",
                "origin": "MHD",
                "destination": "IKA",
                "departure": -3,
                "duration": 1.5,
                "status": "ARRIVED",
            },
            {
                "number": "EP601",
                "airline": "EP",
                "aircraft": "EP-ASA",
                "origin": "SYZ",
                "destination": "IKA",
                "departure": -1,
                "duration": 1.5,
                "status": "DEPARTED",
            },
            {
                "number": "IR722",
                "airline": "IR",
                "aircraft": "EP-IRB",
                "origin": "IKA",
                "destination": "TBZ",
                "departure": 0.5,
                "duration": 1.25,
                "status": "BOARDING",
            },
            {
                "number": "W5104",
                "airline": "W5",
                "aircraft": "EP-MHB",
                "origin": "IKA",
                "destination": "MHD",
                "departure": 1,
                "duration": 1.5,
                "status": "DELAYED",
                "delay": 45,
                "reason": (
                    "Late inbound aircraft due "
                    "to adverse weather."
                ),
            },
            {
                "number": "EP603",
                "airline": "EP",
                "aircraft": "EP-ASB",
                "origin": "IKA",
                "destination": "SYZ",
                "departure": 2,
                "duration": 1.5,
                "status": "SCHEDULED",
            },
            {
                "number": "IR724",
                "airline": "IR",
                "aircraft": "EP-IRA",
                "origin": "MHD",
                "destination": "IKA",
                "departure": 3,
                "duration": 1.5,
                "status": "SCHEDULED",
            },
            {
                "number": "W5106",
                "airline": "W5",
                "aircraft": "EP-MHA",
                "origin": "IKA",
                "destination": "SYZ",
                "departure": 4,
                "duration": 1.5,
                "status": "SCHEDULED",
            },
            {
                "number": "EP605",
                "airline": "EP",
                "aircraft": "EP-ASA",
                "origin": "TBZ",
                "destination": "IKA",
                "departure": 5,
                "duration": 1.5,
                "status": "DELAYED",
                "delay": 30,
                "reason": (
                    "Operational turnaround delay."
                ),
            },
            {
                "number": "IR726",
                "airline": "IR",
                "aircraft": "EP-IRB",
                "origin": "IKA",
                "destination": "MHD",
                "departure": 7,
                "duration": 1.5,
                "status": "SCHEDULED",
            },
            {
                "number": "W5108",
                "airline": "W5",
                "aircraft": "EP-MHB",
                "origin": "MHD",
                "destination": "IKA",
                "departure": 9,
                "duration": 1.5,
                "status": "CANCELLED",
                "reason": (
                    "Flight cancelled due to "
                    "operational restrictions."
                ),
            },
            {
                "number": "EP607",
                "airline": "EP",
                "aircraft": "EP-ASB",
                "origin": "IKA",
                "destination": "TBZ",
                "departure": 12,
                "duration": 1.25,
                "status": "SCHEDULED",
            },
        ]

        flights = {}

        for item in flight_data:
            departure = now + timedelta(
                hours=item["departure"]
            )

            arrival = departure + timedelta(
                hours=item["duration"]
            )

            status = item["status"]

            delay_minutes = item.get(
                "delay",
                0,
            )

            estimated_departure = None
            estimated_arrival = None
            actual_departure = None
            actual_arrival = None

            if status == "DELAYED":
                estimated_departure = (
                    departure
                    + timedelta(
                        minutes=delay_minutes
                    )
                )

                estimated_arrival = (
                    arrival
                    + timedelta(
                        minutes=delay_minutes
                    )
                )

            if status == "DEPARTED":
                actual_departure = (
                    departure
                    + timedelta(minutes=5)
                )

            if status == "ARRIVED":
                actual_departure = (
                    departure
                    + timedelta(minutes=4)
                )

                actual_arrival = (
                    arrival
                    + timedelta(minutes=8)
                )

            flight, _ = (
                Flight.objects.update_or_create(
                    flight_number=item[
                        "number"
                    ],
                    defaults={
                        "airline": airlines[
                            item["airline"]
                        ],
                        "aircraft": aircraft[
                            item["aircraft"]
                        ],
                        "origin": airports[
                            item["origin"]
                        ],
                        "destination": airports[
                            item["destination"]
                        ],
                        "departure_time": departure,
                        "arrival_time": arrival,
                        "status": status,
                        "estimated_departure_time": (
                            estimated_departure
                        ),
                        "estimated_arrival_time": (
                            estimated_arrival
                        ),
                        "actual_departure_time": (
                            actual_departure
                        ),
                        "actual_arrival_time": (
                            actual_arrival
                        ),
                        "disruption_reason": (
                            item.get(
                                "reason",
                                "",
                            )
                        ),
                        "status_updated_at": now,
                    },
                )
            )

            flights[item["number"]] = flight

        self.stdout.write(
            self.style.SUCCESS(
                f"Flights: {len(flights)}"
            )
        )

        return flights

    def create_gate_assignments(
        self,
        now,
        flights,
        gates,
    ):
        assignments = [
            (
                "IR720",
                "MHD-A01",
                "RELEASED",
            ),
            (
                "W5102",
                "IKA-A01",
                "RELEASED",
            ),
            (
                "EP601",
                "SYZ-A01",
                "RELEASED",
            ),
            (
                "IR722",
                "IKA-A02",
                "ACTIVE",
            ),
            (
                "W5104",
                "IKA-A03",
                "ACTIVE",
            ),
            (
                "EP603",
                "IKA-B01",
                "ACTIVE",
            ),
            (
                "EP605",
                "TBZ-A01",
                "ACTIVE",
            ),
        ]

        for (
            flight_number,
            gate_code,
            status,
        ) in assignments:
            released_time = None

            if status == "RELEASED":
                released_time = now

            GateAssignment.objects.update_or_create(
                flight=flights[flight_number],
                gate=gates[gate_code],
                defaults={
                    "status": status,
                    "released_time": released_time,
                    "notes": (
                        "Demo operational "
                        "gate assignment."
                    ),
                },
            )

    def create_ground_operations(
        self,
        now,
        flights,
        users,
        operation_types,
    ):
        ground_staff = users["demo_ground"]

        data = [
            (
                "IR722",
                "Baggage Handling",
                "IN_PROGRESS",
            ),
            (
                "IR722",
                "Refueling",
                "COMPLETED",
            ),
            (
                "IR722",
                "Cabin Cleaning",
                "COMPLETED",
            ),
            (
                "W5104",
                "Baggage Handling",
                "IN_PROGRESS",
            ),
            (
                "W5104",
                "Refueling",
                "COMPLETED",
            ),
            (
                "W5104",
                "Technical Inspection",
                "IN_PROGRESS",
            ),
            (
                "EP603",
                "Catering",
                "PENDING",
            ),
            (
                "EP603",
                "Baggage Handling",
                "PENDING",
            ),
            (
                "EP605",
                "Technical Inspection",
                "IN_PROGRESS",
            ),
            (
                "IR726",
                "Catering",
                "PENDING",
            ),
            (
                "IR726",
                "Pushback",
                "PENDING",
            ),
        ]

        for (
            flight_number,
            operation_name,
            status,
        ) in data:
            start_time = None
            end_time = None

            if status in {
                "IN_PROGRESS",
                "COMPLETED",
            }:
                start_time = (
                    now - timedelta(minutes=30)
                )

            if status == "COMPLETED":
                end_time = (
                    now - timedelta(minutes=5)
                )

            GroundOperation.objects.update_or_create(
                flight=flights[flight_number],
                operation_type=(
                    operation_types[
                        operation_name
                    ]
                ),
                defaults={
                    "assigned_staff": ground_staff,
                    "status": status,
                    "start_time": start_time,
                    "end_time": end_time,
                    "notes": (
                        "Demo turnaround "
                        "operation."
                    ),
                },
            )

    def create_security_reports(
        self,
        flights,
        users,
    ):
        officer = users["demo_security"]

        data = [
            (
                "W5104",
                "BAGGAGE",
                "MEDIUM",
                "INVESTIGATING",
                (
                    "Unattended baggage reported "
                    "near the boarding area."
                ),
            ),
            (
                "IR722",
                "ACCESS",
                "LOW",
                "RESOLVED",
                (
                    "Restricted access badge "
                    "verification completed."
                ),
            ),
            (
                "EP603",
                "PASSENGER",
                "HIGH",
                "OPEN",
                (
                    "Passenger document mismatch "
                    "requires secondary review."
                ),
            ),
            (
                "IR726",
                "AIRCRAFT",
                "MEDIUM",
                "OPEN",
                (
                    "Pre-departure aircraft "
                    "security inspection requested."
                ),
            ),
        ]

        for (
            flight_number,
            report_type,
            severity,
            status,
            description,
        ) in data:
            SecurityReport.objects.update_or_create(
                flight=flights[flight_number],
                report_type=report_type,
                description=description,
                defaults={
                    "officer": officer,
                    "severity": severity,
                    "status": status,
                },
            )

    def create_passenger_requests(
        self,
        flights,
        users,
    ):
        staff = users["demo_passenger"]

        data = [
            (
                "IR722",
                "Sara Mohammadi",
                "WHEELCHAIR",
                "HIGH",
                "ASSIGNED",
                "Wheelchair required at gate.",
            ),
            (
                "W5104",
                "Ali Rezaei",
                "SPECIAL_ASSISTANCE",
                "URGENT",
                "IN_PROGRESS",
                (
                    "Passenger requires priority "
                    "boarding assistance."
                ),
            ),
            (
                "EP603",
                "Neda Karimi",
                "LOST_FOUND",
                "MEDIUM",
                "OPEN",
                (
                    "Passenger reported a missing "
                    "carry-on item."
                ),
            ),
            (
                "EP605",
                "Arash Ahmadi",
                "COMPLAINT",
                "MEDIUM",
                "ASSIGNED",
                (
                    "Passenger requested support "
                    "regarding flight delay."
                ),
            ),
            (
                "IR726",
                "Mina Hosseini",
                "WHEELCHAIR",
                "HIGH",
                "ASSIGNED",
                (
                    "Mobility assistance requested "
                    "for departure."
                ),
            ),
        ]

        for (
            flight_number,
            passenger_name,
            request_type,
            priority,
            status,
            description,
        ) in data:
            PassengerRequest.objects.update_or_create(
                flight=flights[flight_number],
                passenger_name=passenger_name,
                request_type=request_type,
                defaults={
                    "priority": priority,
                    "description": description,
                    "status": status,
                    "assigned_staff": staff,
                },
            )

    def create_notifications(
        self,
        flights,
        users,
    ):
        notifications = [
            (
                "demo_admin",
                "Flight W5104 delayed",
                (
                    "Flight W5104 has been delayed "
                    "by 45 minutes."
                ),
                "WARNING",
            ),
            (
                "demo_ground",
                "Turnaround action required",
                (
                    "Ground operations for W5104 "
                    "require attention."
                ),
                "WARNING",
            ),
            (
                "demo_security",
                "Security review assigned",
                (
                    "Security report for EP603 "
                    "requires investigation."
                ),
                "ERROR",
            ),
            (
                "demo_passenger",
                "Urgent passenger assistance",
                (
                    "Urgent passenger request "
                    "exists for W5104."
                ),
                "WARNING",
            ),
            (
                "demo_iran_operator",
                "IR722 boarding",
                (
                    "Flight IR722 is currently "
                    "boarding."
                ),
                "INFO",
            ),
            (
                "demo_mahan_operator",
                "W5104 delayed",
                (
                    "Operational delay registered "
                    "for flight W5104."
                ),
                "WARNING",
            ),
        ]

        for (
            username,
            title,
            message,
            notification_type,
        ) in notifications:
            Notification.objects.update_or_create(
                user=users[username],
                title=title,
                defaults={
                    "message": message,
                    "notification_type": (
                        notification_type
                    ),
                    "is_read": False,
                },
            )

    def create_audit_logs(
        self,
        flights,
        users,
    ):
        admin = users["demo_admin"]

        audit_data = [
            (
                "IR722",
                AuditLog.Action.STATUS_CHANGE,
                (
                    "Flight IR722 changed from "
                    "SCHEDULED to BOARDING."
                ),
                {
                    "status": {
                        "from": "SCHEDULED",
                        "to": "BOARDING",
                    }
                },
            ),
            (
                "W5104",
                AuditLog.Action.STATUS_CHANGE,
                (
                    "Flight W5104 changed from "
                    "SCHEDULED to DELAYED."
                ),
                {
                    "status": {
                        "from": "SCHEDULED",
                        "to": "DELAYED",
                    },
                    "delay_minutes": {
                        "from": None,
                        "to": 45,
                    },
                },
            ),
            (
                "EP601",
                AuditLog.Action.STATUS_CHANGE,
                (
                    "Flight EP601 changed from "
                    "BOARDING to DEPARTED."
                ),
                {
                    "status": {
                        "from": "BOARDING",
                        "to": "DEPARTED",
                    }
                },
            ),
            (
                "W5108",
                AuditLog.Action.STATUS_CHANGE,
                (
                    "Flight W5108 was cancelled "
                    "due to operational restrictions."
                ),
                {
                    "status": {
                        "from": "SCHEDULED",
                        "to": "CANCELLED",
                    }
                },
            ),
        ]

        for (
            flight_number,
            action,
            description,
            changes,
        ) in audit_data:
            flight = flights[flight_number]

            AuditLog.objects.update_or_create(
                entity_type=(
                    AuditLog.EntityType.FLIGHT
                ),
                entity_id=str(flight.pk),
                description=description,
                defaults={
                    "actor": admin,
                    "action": action,
                    "changes": changes,
                    "ip_address": "127.0.0.1",
                },
            )

    def print_summary(self, password):
        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Demo dataset is ready."
            )
        )

        self.stdout.write("")
        self.stdout.write(
            self.style.WARNING(
                "Demo credentials"
            )
        )

        usernames = [
            "demo_admin",
            "demo_manager",
            "demo_ground",
            "demo_security",
            "demo_passenger",
            "demo_iran_operator",
            "demo_mahan_operator",
        ]

        for username in usernames:
            self.stdout.write(
                f"  {username}"
            )

        self.stdout.write("")
        self.stdout.write(
            "All demo users use the password "
            "provided with --password."
        )

        self.stdout.write("")
        self.stdout.write(
            "Suggested pages to verify:"
        )
        self.stdout.write(
            "  /dashboard/"
        )
        self.stdout.write(
            "  /flights/"
        )
        self.stdout.write(
            "  /flights/board/"
        )
        self.stdout.write(
            "  /operations/"
        )
        self.stdout.write(
            "  /notifications/"
        )