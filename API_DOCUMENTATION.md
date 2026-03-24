# Conversation Management API Documentation

## Base URL
```
http://127.0.0.1:1000/api/conversations/
```

## Authentication
All endpoints require the user to be logged in (using Django session authentication).

---

## Endpoints

### 1. Update Conversation Status
**Endpoint:** `/api/conversations/<id>/status/`  
**Method:** `PATCH`  
**Description:** Change conversation status

**Payload:**
```json
{
  "status": "active|idle|awaiting_response|resolved|archived"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Conversation status updated to active.",
  "conversation_id": 123,
  "new_status": "active"
}
```

---

### 2. Update Urgency Score
**Endpoint:** `/api/conversations/<id>/urgency/`  
**Method:** `PATCH`  
**Description:** Set urgency score (1-10)

**Payload:**
```json
{
  "urgency_score": 8
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Urgency score updated to 8.",
  "conversation_id": 123,
  "urgency_score": 8
}
```

---

### 3. Assign Conversation to Team Member
**Endpoint:** `/api/conversations/<id>/assign/`  
**Method:** `PATCH`  
**Description:** Assign conversation to a user

**Payload:**
```json
{
  "assigned_to": 5
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Conversation assigned to John Doe.",
  "conversation_id": 123,
  "assigned_to": "John Doe"
}
```

---

### 4. Schedule Follow-up
**Endpoint:** `/api/conversations/<id>/followup/`  
**Method:** `PATCH`  
**Description:** Schedule a follow-up reminder

**Payload:**
```json
{
  "follow_up_date": "2026-02-20T14:30:00Z"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Follow-up scheduled for 2026-02-20 14:30.",
  "conversation_id": 123,
  "follow_up_date": "2026-02-20 14:30"
}
```

---

### 5. Update Category
**Endpoint:** `/api/conversations/<id>/category/`  
**Method:** `PATCH`  
**Description:** Set conversation category

**Payload:**
```json
{
  "category": "inquiry|complaint|feedback|support|order_related|return|other"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Category updated to complaint.",
  "conversation_id": 123,
  "category": "complaint"
}
```

---

### 6. Update Sentiment
**Endpoint:** `/api/conversations/<id>/sentiment/`  
**Method:** `PATCH`  
**Description:** Set conversation sentiment

**Payload:**
```json
{
  "sentiment": "happy|neutral|frustrated"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Sentiment updated to frustrated.",
  "conversation_id": 123,
  "sentiment": "frustrated"
}
```

---

### 7. Manage Tags
**Endpoint:** `/api/conversations/<id>/tags/`  
**Methods:** `PATCH` (add), `DELETE` (remove)  
**Description:** Add or remove tags from conversation

**Add Tag (PATCH):**
```json
{
  "tag_name": "urgent"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Tag \"urgent\" added.",
  "conversation_id": 123,
  "tag_id": 5,
  "tag_name": "urgent"
}
```

**Remove Tag (DELETE):**
```json
{
  "tag_id": 5
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Tag \"urgent\" removed.",
  "conversation_id": 123
}
```

---

### 8. Update Customer Segment
**Endpoint:** `/api/conversations/<id>/segment/`  
**Method:** `PATCH`  
**Description:** Set customer segment

**Payload:**
```json
{
  "customer_segment": "vip|repeat_buyer|high_value|new_customer|at_risk|regular"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Customer segment updated to vip.",
  "conversation_id": 123,
  "segment": "vip"
}
```

---

### 9. Mark as Resolved
**Endpoint:** `/api/conversations/<id>/resolve/`  
**Method:** `PATCH`  
**Description:** Mark conversation as resolved or reopen it

**Payload:**
```json
{
  "is_resolved": true
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Marked as resolved",
  "conversation_id": 123,
  "is_resolved": true
}
```

---

## Testing with cURL

```bash
# Update Status
curl -X PATCH http://127.0.0.1:1000/api/conversations/1/status/ \
  -H "Content-Type: application/json" \
  -d '{"status": "resolved"}' \
  --cookie "sessionid=YOUR_SESSION_ID"

# Add Tag
curl -X PATCH http://127.0.0.1:1000/api/conversations/1/tags/ \
  -H "Content-Type: application/json" \
  -d '{"tag_name": "vip_customer"}' \
  --cookie "sessionid=YOUR_SESSION_ID"

# Update Urgency
curl -X PATCH http://127.0.0.1:1000/api/conversations/1/urgency/ \
  -H "Content-Type: application/json" \
  -d '{"urgency_score": 9}' \
  --cookie "sessionid=YOUR_SESSION_ID"
```

---

## Testing with JavaScript Fetch API

```javascript
// Helper function to get CSRF token
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// Update Status
fetch('/api/conversations/1/status/', {
  method: 'PATCH',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': getCookie('csrftoken')
  },
  body: JSON.stringify({ status: 'resolved' })
})
.then(response => response.json())
.then(data => console.log(data));

// Add Tag
fetch('/api/conversations/1/tags/', {
  method: 'PATCH',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': getCookie('csrftoken')
  },
  body: JSON.stringify({ tag_name: 'priority' })
})
.then(response => response.json())
.then(data => console.log(data));

// Update Urgency
fetch('/api/conversations/1/urgency/', {
  method: 'PATCH',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': getCookie('csrftoken')
  },
  body: JSON.stringify({ urgency_score: 9 })
})
.then(response => response.json())
.then(data => console.log(data));
```

---

## Error Responses

All errors follow this format:

```json
{
  "status": "error",
  "message": "Error description here"
}
```

**Common Error Codes:**
- `400` - Bad Request (invalid data)
- `404` - Not Found (conversation not found)
- `500` - Server Error

---

## Statuses

| Value | Display |
|-------|---------|
| `active` | Active |
| `idle` | Idle |
| `awaiting_response` | Awaiting Response |
| `resolved` | Resolved |
| `archived` | Archived |

## Categories

| Value | Display |
|-------|---------|
| `inquiry` | Inquiry |
| `complaint` | Complaint |
| `feedback` | Feedback |
| `support` | Support |
| `order_related` | Order Related |
| `return` | Return |
| `other` | Other |

## Sentiments

| Value | Emoji |
|-------|-------|
| `happy` | 😊 |
| `neutral` | 😐 |
| `frustrated` | 😞 |

## Customer Segments

| Value | Icon |
|-------|------|
| `vip` | ⭐ |
| `repeat_buyer` | 🔄 |
| `high_value` | 💎 |
| `new_customer` | 👤 |
| `at_risk` | ⚠️ |
| `regular` | 👥 |

---

## Notes

- All endpoints require authentication
- `conversation_id` must be a participant in the conversation
- CSRF token is required for POST/PATCH/DELETE requests
- Datetime fields should be in ISO 8601 format (e.g., `2026-02-20T14:30:00Z`)
- All responses include a `status` field: either `"success"` or `"error"`
