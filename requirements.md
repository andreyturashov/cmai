# 🧠 Code Mentor — Full Product & Technical Specification

---

# 📌 1. Product Overview

A platform where developers improve **code review skills** by:

- Reviewing realistic PRs
- Adding inline comments
- Classifying issues (critical / medium / low)
- Suggesting fixes
- Receiving AI-based evaluation

---

# 🎯 Target Audience

- Beginner backend developers
- Mid-level engineers preparing for interviews
- Developers lacking real PR review experience

---

# 🧭 Core Value

> Train engineering judgment, not just coding.

---

# 🖥️ UI/UX Layout

## Main Layout

---------------------------------------------------------
| Left Panel            | Right Panel                   |
|-----------------------|-------------------------------|
| PR Info               | Code Viewer                  |
| Requirements          | Inline Comments              |
| Task Instructions     | Comment Interaction          |
---------------------------------------------------------

---

# LEFT PANEL — PR Context

## PR Title
Add endpoint to create orders

## PR Description
This endpoint allows users to create an order. Basic functionality implemented.

## Requirements
- Validate user input
- Ensure total price correctness
- Handle errors properly
- Follow clean architecture practices

## Instructions
1. Review the code
2. Add inline comments
3. Assign severity
4. Suggest improvements
5. (Optional) Provide fixed code

---

# RIGHT PANEL — Code + Comments

## Code Viewer
- Syntax highlighting
- Line numbers
- Read-only
- Scrollable

## Inline Comments
User clicks line → adds comment

Example:
Line 15: Missing validation

---

# AI Evaluation

Score: 7.5 / 10  
Detected: 2/3 critical issues  
Missed: validation, error handling  

---

# Backend

Entities:
- Task
- Issue
- UserReview

---

# API

GET /tasks  
GET /tasks/{id}  
POST /reviews  
POST /evaluate  

---

# Tech Stack

Backend: FastAPI  
Frontend: React + Vite  
AI: OpenAI API  

---

# Monetization

Free: limited tasks  
Paid: full AI review  

---

# MVP

- Static tasks  
- Inline comments  
- AI feedback  

---

# Execution Plan

Week 1: UI  
Week 2: Backend  
Week 3: AI  
Week 4: Launch
