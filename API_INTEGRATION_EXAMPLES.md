# API Integration Examples

## JavaScript Functions Already Integrated in Template

All these functions are already available in `vendor_conversation_list.html` and ready to use:

### Status Management
```javascript
// Change conversation status
changeConversationStatus(conversationId, 'resolved');
changeConversationStatus(conversationId, 'awaiting_response');
changeConversationStatus(conversationId, 'idle');
changeConversationStatus(conversationId, 'archived');
changeConversationStatus(conversationId, 'active');
```

### Urgency Scoring
```javascript
// Update urgency (1-10)
updateUrgencyScore(conversationId, 5);
updateUrgencyScore(conversationId, 9);  // High urgency
updateUrgencyScore(conversationId, 2);  // Low urgency
```

### Team Assignment
```javascript
// Assign to team member (by user ID)
assignConversationTo(conversationId, 5);
assignConversationTo(conversationId, 8);
```

### Follow-up Scheduling
```javascript
// Schedule follow-up (ISO 8601 datetime)
scheduleFollowUp(conversationId, '2026-02-20T14:30:00Z');
scheduleFollowUp(conversationId, '2026-03-01T09:00:00Z');
```

### Category Management
```javascript
// Change category
changeCategory(conversationId, 'complaint');
changeCategory(conversationId, 'inquiry');
changeCategory(conversationId, 'feedback');
changeCategory(conversationId, 'support');
changeCategory(conversationId, 'order_related');
changeCategory(conversationId, 'return');
```

### Sentiment Analysis
```javascript
// Set sentiment
setSentiment(conversationId, 'frustrated');
setSentiment(conversationId, 'neutral');
setSentiment(conversationId, 'happy');
```

### Tag Management
```javascript
// Add tag to conversation
fetch(`/api/conversations/${conversationId}/tags/`, {
  method: 'PATCH',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': getCookie('csrftoken')
  },
  body: JSON.stringify({ tag_name: 'urgent' })
}).then(r => r.json()).then(d => console.log(d));

// Remove tag from conversation
removeTag(conversationId, tagId, element);
```

### Customer Segment
```javascript
// Set customer segment
setCustomerSegment(conversationId, 'vip');
setCustomerSegment(conversationId, 'repeat_buyer');
setCustomerSegment(conversationId, 'high_value');
setCustomerSegment(conversationId, 'new_customer');
setCustomerSegment(conversationId, 'at_risk');
setCustomerSegment(conversationId, 'regular');
```

### Resolution
```javascript
// Mark as resolved
markAsResolved(conversationId);

// Reopen conversation
fetch(`/api/conversations/${conversationId}/resolve/`, {
  method: 'PATCH',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': getCookie('csrftoken')
  },
  body: JSON.stringify({ is_resolved: false })
}).then(r => r.json()).then(d => console.log(d));
```

### Filtering
```javascript
// Quick filter functions
filterByStatus('resolved');
filterByStatus('awaiting_response');

filterBySegment('vip');
filterBySegment('high_value');

filterByUrgency(7);  // Min urgency score
filterByCategory('complaint');

clearAllFilters();  // Reset filters
```

---

## Custom Implementation Examples

### Example 1: Create a Status Dropdown Menu

```html
<select onchange="changeConversationStatus(123, this.value)">
  <option value="active">Active</option>
  <option value="idle">Idle</option>
  <option value="awaiting_response">Awaiting Response</option>
  <option value="resolved">Resolved</option>
  <option value="archived">Archived</option>
</select>
```

### Example 2: Create an Urgency Slider

```html
<input type="range" min="1" max="10" value="5" 
  onchange="updateUrgencyScore(123, this.value)">
<span id="urgency-display">5</span>/10

<script>
  const slider = document.querySelector('input[type="range"]');
  slider.addEventListener('input', (e) => {
    document.getElementById('urgency-display').textContent = e.target.value;
    updateUrgencyScore(123, e.target.value);
  });
</script>
```

### Example 3: Create a Category Quick-Select Menu

```html
<div class="category-selector">
  <button onclick="changeCategory(123, 'inquiry')">📝 Inquiry</button>
  <button onclick="changeCategory(123, 'complaint')">😞 Complaint</button>
  <button onclick="changeCategory(123, 'feedback')">⭐ Feedback</button>
  <button onclick="changeCategory(123, 'support')">🆘 Support</button>
  <button onclick="changeCategory(123, 'order_related')">📦 Order</button>
  <button onclick="changeCategory(123, 'return')">↩️ Return</button>
</div>
```

### Example 4: Create a Sentiment Selector

```html
<div class="sentiment-selector">
  <button onclick="setSentiment(123, 'happy')">😊 Happy</button>
  <button onclick="setSentiment(123, 'neutral')">😐 Neutral</button>
  <button onclick="setSentiment(123, 'frustrated')">😞 Frustrated</button>
</div>
```

### Example 5: Create a Quick Assignment Panel

```html
<div class="team-members">
  <!-- Assuming team members data is available -->
  <button onclick="assignConversationTo(123, 4)" class="team-member">
    <img src="/media/profile/user4.jpg" alt="John">
    <span>John Doe</span>
  </button>
  <button onclick="assignConversationTo(123, 5)" class="team-member">
    <img src="/media/profile/user5.jpg" alt="Jane">
    <span>Jane Smith</span>
  </button>
</div>
```

### Example 6: Create a Tag Input Field

```html
<div class="tag-input">
  <input type="text" id="new-tag" placeholder="Add a tag...">
  <button onclick="addTagFromInput(123)">Add Tag</button>
</div>

<script>
  function addTagFromInput(conversationId) {
    const input = document.getElementById('new-tag');
    const tagName = input.value.trim();
    
    if (!tagName) return;
    
    fetch(`/api/conversations/${conversationId}/tags/`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify({ tag_name: tagName })
    })
    .then(r => r.json())
    .then(d => {
      if (d.status === 'success') {
        input.value = '';
        console.log('Tag added:', d.tag_name);
        location.reload(); // Or update DOM dynamically
      }
    })
    .catch(e => console.error('Error:', e));
  }
</script>
```

### Example 7: Create a Follow-up Scheduler

```html
<div class="followup-scheduler">
  <input type="datetime-local" id="followup-date">
  <button onclick="scheduleFollowUpFromInput(123)">Schedule Follow-up</button>
</div>

<script>
  function scheduleFollowUpFromInput(conversationId) {
    const dateInput = document.getElementById('followup-date');
    const dateValue = dateInput.value;
    
    if (!dateValue) {
      alert('Please select a date and time');
      return;
    }
    
    // Convert to ISO 8601 format
    const date = new Date(dateValue);
    const isoDate = date.toISOString();
    
    scheduleFollowUp(conversationId, isoDate);
  }
</script>
```

### Example 8: Create a Bulk Action for Selected Conversations

```html
<div class="bulk-actions">
  <button onclick="bulkUpdateStatus('resolved')">Mark All Selected as Resolved</button>
  <button onclick="bulkSetUrgency(9)">Set All Selected as High Priority</button>
</div>

<script>
  function bulkUpdateStatus(status) {
    const selected = document.querySelectorAll('.conversation-checkbox:checked');
    
    selected.forEach(checkbox => {
      const conversationId = checkbox.dataset.conversationId;
      changeConversationStatus(conversationId, status);
    });
  }
  
  function bulkSetUrgency(score) {
    const selected = document.querySelectorAll('.conversation-checkbox:checked');
    
    selected.forEach(checkbox => {
      const conversationId = checkbox.dataset.conversationId;
      updateUrgencyScore(conversationId, score);
    });
  }
</script>
```

### Example 9: Create a Search + Filter Bar

```html
<div class="filter-bar">
  <input type="text" id="search" placeholder="Search conversations..." onkeyup="handleSearch(this.value)">
  
  <select onchange="filterByStatus(this.value)">
    <option value="">All Status</option>
    <option value="active">Active</option>
    <option value="awaiting_response">Awaiting Response</option>
    <option value="resolved">Resolved</option>
  </select>
  
  <select onchange="filterBySegment(this.value)">
    <option value="">All Customers</option>
    <option value="vip">VIP</option>
    <option value="repeat_buyer">Repeat Buyer</option>
    <option value="high_value">High Value</option>
  </select>
  
  <button onclick="clearAllFilters()">Clear Filters</button>
</div>

<script>
  function handleSearch(query) {
    // Implement custom search logic
    const url = new URL(window.location);
    if (query) {
      url.searchParams.set('q', query);
    } else {
      url.searchParams.delete('q');
    }
    window.history.pushState({}, '', url);
    // Could also filter DOM directly without page reload
  }
</script>
```

### Example 10: Create a Real-time Status Indicator

```html
<div class="status-monitor">
  <div class="status-group">
    <h3>Active</h3>
    <span class="count" id="count-active">0</span>
  </div>
  <div class="status-group">
    <h3>Awaiting Response</h3>
    <span class="count" id="count-awaiting">0</span>
  </div>
  <div class="status-group">
    <h3>Overdue SLA</h3>
    <span class="count alert" id="count-overdue">0</span>
  </div>
</div>

<script>
  function updateStatusCounts() {
    const counts = {
      active: document.querySelectorAll('.status-badge.status-active').length,
      awaiting: document.querySelectorAll('.status-badge.status-awaiting_response').length,
      overdue: document.querySelectorAll('.sla-indicator.sla-overdue').length
    };
    
    document.getElementById('count-active').textContent = counts.active;
    document.getElementById('count-awaiting').textContent = counts.awaiting;
    document.getElementById('count-overdue').textContent = counts.overdue;
  }
  
  // Update on page load
  updateStatusCounts();
  
  // Update every 30 seconds
  setInterval(updateStatusCounts, 30000);
</script>
```

---

## Error Handling Best Practices

```javascript
async function safeAPICall(endpoint, method, data) {
  try {
    const response = await fetch(endpoint, {
      method: method,
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify(data)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || `HTTP ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error(`API Error: ${error.message}`);
    // Show user-friendly notification
    showNotification(`Error: ${error.message}`, 'error');
    return null;
  }
}

// Usage
const result = await safeAPICall(
  '/api/conversations/1/status/',
  'PATCH',
  { status: 'resolved' }
);

if (result) {
  console.log('Success:', result);
}
```

---

## Testing from Browser Console

```javascript
// Test all conversation APIs

// 1. Update status
fetch('/api/conversations/1/status/', {
  method: 'PATCH',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': getCookie('csrftoken')
  },
  body: JSON.stringify({ status: 'resolved' })
}).then(r => r.json()).then(d => console.log('Status:', d));

// 2. Update urgency
fetch('/api/conversations/1/urgency/', {
  method: 'PATCH',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': getCookie('csrftoken')
  },
  body: JSON.stringify({ urgency_score: 8 })
}).then(r => r.json()).then(d => console.log('Urgency:', d));

// 3. Add tag
fetch('/api/conversations/1/tags/', {
  method: 'PATCH',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': getCookie('csrftoken')
  },
  body: JSON.stringify({ tag_name: 'vip_customer' })
}).then(r => r.json()).then(d => console.log('Tag:', d));

// 4. Assign to user
fetch('/api/conversations/1/assign/', {
  method: 'PATCH',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': getCookie('csrftoken')
  },
  body: JSON.stringify({ assigned_to: 5 })
}).then(r => r.json()).then(d => console.log('Assignment:', d));

// 5. Mark as resolved
fetch('/api/conversations/1/resolve/', {
  method: 'PATCH',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': getCookie('csrftoken')
  },
  body: JSON.stringify({ is_resolved: true })
}).then(r => r.json()).then(d => console.log('Resolved:', d));
```

---

## Notes

- All API functions automatically reload the page on success (you can customize this)
- CSRF token is required and automatically fetched
- Errors are logged to console
- JSON responses include `status` field: "success" or "error"
- All operations are user-scoped (users can only modify their own conversations)
- Real-time updates would require WebSocket integration (future enhancement)

