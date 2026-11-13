🚧 Status: In development. Hosted on Render.

Overview

This repository contains the backend service for Backbone. It acts as a secure bridge between the client app (Flet) and the PostgreSQL database. By keeping the database credentials only on the server, user data remains secure.

The API handles account creation, secure login with bcrypt hashing, token-based session management, and the core logic for tracking exercises and Personal Records (PRs).

Tech Stack

Python & Flask: Core API framework.

PostgreSQL & psycopg2: Relational database and adapter.

bcrypt & itsdangerous: Password hashing and secure token generation.

Docker Compose: Containerized environment structure.

API Endpoints

The API is currently live Hosted by Render

Authentication

Tokens are valid for 24 hours and must be passed in the Authorization header as Bearer <token> for all protected routes.

POST /register - Creates a new user. Expects JSON: {"username": "...", "password": "..."}. Returns 201 Created with user_id.

POST /login - Authenticates a user. Expects JSON: {"username": "...", "password": "..."}. Returns 200 OK with a signed JWT token.

Protected Routes (Require Token)

User

GET /me - Verifies the current token and returns the user_id.

Exercises

GET /exercises - Returns a list of all available exercises and their respective muscle groups.

Personal Records (PRs)

GET /prs - Retrieves a dictionary of all PRs for the authenticated user, organized by exercise name.

GET /prs/group/<muscle_group> - Retrieves PRs filtered by a specific muscle group (e.g., chest, legs).

POST /prs - Logs a new PR. Expects JSON: {"exercise_id": 1, "weight": 85, "reps": 6, "date": "YYYY-MM-DD"}. Returns 201 Created.

DELETE /prs/<pr_id> - Deletes a specific PR by its ID.

DELETE /exercises/<exercise_id>/prs - Deletes all PRs associated with a specific exercise for the current user.

System

GET /health - Health check endpoint. Returns {"status": "ok"}.

Database Schema

The API structure relies on the following relational tables (with cascading deletes):

users: id, username (unique), hash

exercises: id, name (unique), muscle_group

prs: id, user_id, exercise_id, weight, reps, date

The database comes pre-populated with a wide variety of exercises divided into anatomical categories (chest, legs, glutes, calves, shoulders, back, biceps, triceps, forearms, core, and traps).
