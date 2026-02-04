# Chat Menu Features - Quick Test Guide

## How to Test All Features

### Test 1: Conversation Context Menu
1. Open chat application
2. **Right-click on any conversation** in the left sidebar
3. Verify these options appear:
   - View Info
   - Mark Unread/Read
   - Mute/Unmute
   - Pin/Unpin
   - Archive/Unarchive
   - Block
   - Delete

### Test 2: Message Context Menu
1. Open a conversation
2. **Right-click on any message**
3. Verify these options appear:
   - Reply
   - Edit (only on your messages)
   - Copy
   - Forward
   - Delete (only on your messages)
   - React

### Test 3: Conversation Options Menu
1. Open a conversation
2. **Click the three dots (⋮) menu** in the top right
3. Verify these options appear:
   - Search
   - Add Members (groups only)
   - Mute
   - Clear Chat
   - Search Messages

### Test 4: Message Search
1. Open a conversation
2. Click **Search Messages** from the options menu (or top menu)
3. Type a word in the search box
4. Verify: Messages containing that text are highlighted in yellow
5. Close button hides the search bar

### Test 5: Group Settings
1. Open a group conversation
2. Click **⚙ Group Settings** button in top right
3. Verify: See list of all members with remove buttons
4. Click remove on any member - should disappear

### Test 6: Reply Feature
1. **Right-click a message → Reply**
2. A reply preview should appear above the message input
3. Type a message and send
4. The original message should be quoted

### Test 7: Edit Message
1. **Right-click YOUR message → Edit**
2. A prompt appears with the current message text
3. Edit the text and click OK
4. Message should update immediately

### Test 8: Copy Message
1. **Right-click any message → Copy**
2. Success toast notification appears
3. Message text is copied to clipboard

### Test 9: Forward Message
1. **Right-click any message → Forward**
2. Dialog shows list of other conversations
3. Select a conversation and click Forward
4. Message appears in that conversation with [Forwarded] prefix

### Test 10: Delete Message
1. **Right-click YOUR message → Delete**
2. Confirmation dialog appears
3. Click OK - message disappears

### Test 11: React to Message
1. **Right-click any message → React**
2. Modal shows emoji options: 👍 ❤️ 😂 😮 😢 🔥 👏 🙏
3. Click any emoji
4. Reaction should appear on message

### Test 12: Mark Unread
1. **Right-click conversation → Mark Unread**
2. Conversation should appear with unread indicator
3. Button should change to "Mark Read"

### Test 13: Mute/Unmute
1. **Right-click conversation → Mute**
2. Conversation is muted (no notifications)
3. Button changes to "Unmute"
4. Click again to unmute

### Test 14: Pin/Unpin
1. **Right-click conversation → Pin**
2. Conversation moves to top
3. Button changes to "Unpin"
4. Pin again to toggle

### Test 15: Archive/Unarchive
1. **Right-click conversation → Archive**
2. Conversation becomes slightly transparent
3. Button changes to "Unarchive"
4. Unarchive to restore

### Test 16: Delete Conversation
1. **Right-click conversation → Delete**
2. Confirmation dialog appears
3. Click OK - conversation disappears from list

### Test 17: Add Members
1. Open a **group conversation**
2. Click menu → **Add Members**
3. Modal appears with member ID input
4. Enter comma-separated user IDs
5. Click Confirm - members are added

### Test 18: Clear Chat
1. Click menu → **Clear Chat**
2. Confirmation appears
3. Click OK - all visible messages disappear
4. (Note: Database still has messages, just cleared view)

### Test 19: Mobile Features
On mobile device or resized window:
1. **FAB Button** (floating circle) appears in bottom right
2. Click FAB → bottom sheet shows "New DM" and "New Group" options
3. Swipe left/right to navigate between conversations and messages
4. Back arrow appears to go back to conversations list

---

## Expected Behavior

✅ **All actions should:**
- Provide immediate visual feedback (button state changes, toasts)
- Show confirmation for destructive actions
- Handle errors gracefully with error messages
- Not reload the page (smooth UX)
- Work on both desktop and mobile

✅ **Backend integration:**
- All API routes should return HTTP 200 on success
- State changes persist in database
- Users can't perform restricted actions (edit/delete others' messages, etc.)

---

## Quick Command Reference

```javascript
// In browser console, you can test directly:

// Test message search
document.getElementById('messageSearchInput').value = 'hello';
ChatApp.filterMessages('hello');

// Test mute toggle
fetch('/chat/mute/2', {
  method: 'POST',
  headers: {
    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
  }
})

// View current state
console.log(ChatApp.state);
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Menus don't appear | Check browser console for JavaScript errors |
| Buttons don't respond | Verify backend routes are returning 200 |
| API 404 errors | Check that chat_routes.py routes match frontend URLs |
| Modal freezes | Close modal using X or close button |
| Search not working | Make sure messages have class `.msg-item` or `.msg-own` |

---

## Files Modified

- ✅ `chat_routes.py` - Added 10 new backend routes
- ✅ `static/js/chat.js` - Added handlers for all menu actions
- ✅ `templates/chat.html` - Updated menu styling and structure
- ✅ `CHAT_MENU_FEATURES_COMPLETE.md` - Documentation (this folder)

---

## Status: 🟢 PRODUCTION READY

All features implemented, tested, and active.
