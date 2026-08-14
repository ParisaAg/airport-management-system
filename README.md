# Airport Management System

[![Django CI](https://github.com/ParisaAg/airport-management-system/actions/workflows/tests.yml/badge.svg)](https://github.com/ParisaAg/airport-management-system/actions/workflows/tests.yml)

A production-oriented airport operations platform built with Django and PostgreSQL.

The system coordinates flights, airlines, aircraft, gates, ground operations, security incidents, passenger services, notifications, and audit events through one role-aware operational environment.

## Core Features

- Role-based access control with seven operational roles
- Airline-level flight and aircraft data isolation
- Validated flight lifecycle transitions
- Delay and cancellation management
- Scheduled, estimated, and actual flight timing
- Live public arrivals and departures board
- Gate assignment, conflict prevention, and automatic release
- Ground-operation assignment and lifecycle tracking
- Security incident investigation workflows
- Passenger-service request workflows
- Operational notification delivery
- Searchable immutable audit trail
- Role-aware dashboard and analytics
- Deterministic connected demo dataset
- Automated CI test suite
- Render and PostgreSQL production configuration

## User Roles

| Role | Responsibility |
|---|---|
| Operations Viewer | Read-only operational access |
| Admin | Full platform administration |
| Airport Manager | Airport-wide operational oversight |
| Airline Operator | Own-airline flights and aircraft |
| Ground Staff | Assigned ground-operation workflows |
| Security Officer | Security incident investigation |
| Passenger Service | Passenger assistance workflows |

## Technology Stack

- Python
- Django 5.2
- PostgreSQL
- Django Templates
- JavaScript
- Chart.js
- WhiteNoise
- Gunicorn
- GitHub Actions
- Render

## Project Modules

```text
accounts/            Authentication, users, roles and demo data
airlines/            Airline management
airports/            Airports, terminals and gates
audit/               Operational audit trail
config/              Settings, URLs, WSGI, ASGI and health check
dashboard/           Landing page and role-aware dashboard
fleet/               Aircraft types and registered aircraft
flights/             Flights, disruptions and gate assignments
notifications/       Operational notification delivery
operations/          Ground-operation workflows
passenger_service/   Passenger assistance workflows
security/            Security incident workflows
static/              CSS, JavaScript and images
templates/           Django templates