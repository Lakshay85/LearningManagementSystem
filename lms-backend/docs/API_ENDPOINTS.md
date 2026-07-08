# LMS API Endpoints

## Base URL

```
http://localhost:3000
```

---

## Authentication

### Student Signup
```
POST /auth/student/signup
```
**Body:**
```json
{
  "email": "student@example.com",
  "password": "password123",
  "firstName": "John",
  "lastName": "Doe"
}
```

---

### Faculty Signup
```
POST /auth/faculty/signup
```
**Body:**
```json
{
  "email": "faculty@example.com",
  "password": "password123",
  "firstName": "Jane",
  "lastName": "Smith",
  "department": "Computer Science",
  "specialization": "Machine Learning",
  "qualification": "Ph.D."
}
```

---

### Login (Unified)
```
POST /auth/login
```
**Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

---

### Logout
```
POST /auth/logout
```
**Headers:**
`Authorization: Bearer <accessToken>`

---

### Get Current User (Me)
```
GET /auth/me
```
**Headers:**
`Authorization: Bearer <accessToken>`

---

### Refresh Token
```
POST /auth/refresh
```
**Body:**
```json
{
  "refreshToken": "token"
}
```

---

### Update Password
```
PUT /auth/update-password
```
**Headers:**
`Authorization: Bearer <accessToken>`
**Body:**
```json
{
  "oldPassword": "password123",
  "newPassword": "newpassword456"
}
```

---

### Update Profile
```
PUT /auth/update-profile
```
**Headers:**
`Authorization: Bearer <accessToken>`
**Body:**
```json
{
  "firstName": "John",
  "lastName": "Doe"
}
```

---

### Delete Account
```
DELETE /auth/delete-account
```
**Headers:**
`Authorization: Bearer <accessToken>`

---

## Videos

### Upload Video (Faculty Only)
```
POST /videos/upload
```
**Headers:**
`Authorization: Bearer <accessToken>`
`Content-Type: multipart/form-data`
**Body (form-data):** `video` (file), `title`, `description`, `category`, `visibility`

---

### Get Public Videos (Student)
```
GET /videos/public
```
**Query Params:** `page`, `limit`, `search`, `category`

---

### Get My Videos (Faculty)
```
GET /videos/my-videos
```
**Headers:**
`Authorization: Bearer <accessToken>`
**Query Params:** `page`, `limit`, `search`

---

### Get Faculty Video Stats
```
GET /videos/my-stats
```
**Headers:**
`Authorization: Bearer <accessToken>`

---

### Get Video Analytics
```
GET /videos/analytics/details
```
**Headers:**
`Authorization: Bearer <accessToken>`

---

## Courses

### Get Published Courses
```
GET /courses/published
```
**Query Params:** `page`, `limit`, `search`, `category`, `level`

---

### Create Course (Faculty)
```
POST /courses
```
**Headers:**
`Authorization: Bearer <accessToken>`
**Body:**
```json
{
  "title": "Title",
  "description": "Desc",
  "category": "Cat",
  "level": "beginner",
  "price": 0
}
```

---

### Enroll in Course (Student)
```
POST /courses/:courseId/enroll
```
**Headers:**
`Authorization: Bearer <accessToken>`

---

### Update Progress (Student)
```
PATCH /courses/:courseId/progress
```
**Headers:**
`Authorization: Bearer <accessToken>`
**Body:** `{"progress": 50}`

---

## Documents

### Get My Documents (Faculty)
```
GET /documents/my-documents
```
**Headers:**
`Authorization: Bearer <accessToken>`
**Query Params:** `visibility`

---

### Preview Document
```
GET /courses/documents/:documentId/preview
```
**Headers:**
`Authorization: Bearer <accessToken>`

---

## Health

### Main Health Check
```
GET /health
```

---

### Database Health Check
```
GET /health/db
```

---

## Enums

- **Roles**: `student`, `teacher`, `admin`
- **Visibility**: `public`, `private`, `unlisted`
- **Levels**: `beginner`, `intermediate`, `advanced`
