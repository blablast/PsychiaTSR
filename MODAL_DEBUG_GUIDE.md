# Modal Debug Guide - Prompts Page

## 🐛 Debug Features Added

The prompts page now includes comprehensive debugging to help identify why the modals aren't working.

### Debug Information Available

#### 1. **Sidebar Debug Panel**
- Shows current modal state in real-time
- Displays all session state variables related to modals
- JSON format for easy reading

#### 2. **Button Click Debug Messages**
- Each Edit/Preview button shows a debug message when clicked
- Confirms button press registration
- Shows which prompt ID was selected

#### 3. **Modal Rendering Debug**
- Displays message when modal rendering function is called
- Confirms modal is being processed
- Shows prompt ID being rendered

#### 4. **Manual Test Button**
- "🧪 Test Modal" button in footer
- Directly triggers edit modal with first available prompt
- Bypasses normal button flow for testing

## 🔍 How to Debug

### Step 1: Check Initial State
1. Open the prompts page
2. Look at the sidebar "🐛 Debug Info" panel
3. Verify initial state shows all `false` values

### Step 2: Test Button Clicks
1. Click any "✏️ Edit" or "👀 Preview" button
2. Watch for debug messages appearing
3. Check sidebar debug panel for state changes

### Step 3: Check Modal Rendering
1. If modal state shows `true` but no modal appears
2. Look for "🐛 DEBUG: Rendering [edit/preview] modal for [prompt_id]"
3. This confirms the rendering function is being called

### Step 4: Use Manual Test
1. Click "🧪 Test Modal" button in footer
2. This bypasses normal button flow
3. Should trigger modal directly

## 🎯 Expected Behavior

### When Edit Button is Clicked:
```json
{
  "edit_modal_open": true,
  "preview_modal_open": false,
  "editing_prompt_id": "prompt_name_here",
  "previewing_prompt_id": null,
  "modal_refresh_key": 0
}
```

### When Preview Button is Clicked:
```json
{
  "edit_modal_open": false,
  "preview_modal_open": true,
  "editing_prompt_id": null,
  "previewing_prompt_id": "prompt_name_here",
  "modal_refresh_key": 0
}
```

## 🔧 Troubleshooting Steps

### If Debug Messages Don't Appear
- **Issue**: Button clicks not registering
- **Solution**: Check for key conflicts or Streamlit caching issues

### If State Changes But No Modal
- **Issue**: Modal rendering function not being called
- **Solution**: Check modal rendering conditions

### If Modal Function Called But No Display
- **Issue**: Modal rendering logic problem
- **Solution**: Check individual tab rendering within modal

### If Everything Shows But Modal Still Hidden
- **Issue**: CSS or Streamlit display issue
- **Solution**: Try refreshing page or clearing browser cache

## 🚨 Common Issues & Solutions

### 1. Session State Not Updating
```python
# Problem: Session state changes not persisting
# Solution: Check if st.rerun() is being called
```

### 2. Multiple Modals Conflicting
```python
# Problem: Both modals trying to open simultaneously
# Solution: Debug panel shows which modals are active
```

### 3. Prompt ID Not Found
```python
# Problem: Invalid prompt_id causing errors
# Solution: Check debug panel for actual prompt_id values
```

## 📋 Debug Checklist

- [ ] Debug panel shows in sidebar
- [ ] Button clicks show debug messages
- [ ] Session state changes when buttons clicked
- [ ] Modal rendering debug messages appear
- [ ] Manual test button works
- [ ] Modals actually display on screen

## 🔄 Next Steps

1. **Test with debug enabled** - Use the debug features to identify exactly where the issue occurs
2. **Check browser console** - Look for JavaScript errors that might prevent modal display
3. **Try manual test button** - Bypass normal flow to test modal rendering directly
4. **Compare session state** - Verify state changes match expected behavior

## 🧹 Cleanup

Once modals are working, the debug features can be removed by:
1. Removing sidebar debug panel
2. Removing button click debug messages
3. Removing modal rendering debug messages
4. Removing manual test button

The debug features are temporary and should be cleaned up once the issue is resolved.