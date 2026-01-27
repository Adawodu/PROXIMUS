# API Reference

Base URL: `http://localhost:8000`

## Health

### GET /health

Check API status.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

## Resumes

### GET /resumes

List all uploaded resumes.

**Response:**
```json
{
  "resumes": [
    {
      "id": "a1b2c3d4e5f6",
      "candidate_name": "Jane Doe",
      "file_path": "/path/to/resume.pdf",
      "created_at": "2025-01-26T12:00:00",
      "content_preview": "Jane Doe\nSoftware Engineer..."
    }
  ],
  "total": 1
}
```

### POST /resumes

Upload a new resume.

**Request:** `multipart/form-data`
- `file` (required) — PDF, DOCX, or TXT file
- `candidate_name` (optional) — Override extracted name

**Response:**
```json
{
  "id": "a1b2c3d4e5f6",
  "candidate_name": "Jane Doe",
  "message": "Resume uploaded successfully for Jane Doe"
}
```

### GET /resumes/{resume_id}

Get a specific resume.

**Response:** Same as individual item in list response.

### DELETE /resumes/{resume_id}

Delete a resume.

**Response:**
```json
{
  "message": "Resume a1b2c3d4e5f6 deleted successfully"
}
```

### GET /resumes/{resume_id}/context

Get the system prompt that the voice agent will use.

**Response:**
```json
{
  "system_prompt": "You are Jane Doe. A recruiter or hiring manager is calling you..."
}
```

### GET /resumes/{resume_id}/phones

Get all phone numbers linked to a resume.

**Response:**
```json
{
  "phones": ["+12481234567"]
}
```

## Phone Links

### POST /phone-links

Link a phone number to a resume.

**Request:**
```json
{
  "phone": "+12481234567",
  "resume_id": "a1b2c3d4e5f6"
}
```

**Response:**
```json
{
  "phone": "+12481234567",
  "resume_id": "a1b2c3d4e5f6",
  "candidate_name": "Jane Doe"
}
```

### GET /phone-links

List all phone-to-resume links.

**Response:**
```json
{
  "links": [
    {
      "phone": "+12481234567",
      "resume_id": "a1b2c3d4e5f6",
      "candidate_name": "Jane Doe"
    }
  ],
  "total": 1
}
```

### GET /phone-links/{phone}

Get the resume linked to a phone number.

### DELETE /phone-links/{phone}

Remove a phone number link.

**Response:**
```json
{
  "message": "Phone link removed for +12481234567"
}
```
