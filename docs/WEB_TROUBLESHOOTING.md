# Web Interface Troubleshooting

## HTTP 403 Error

If you see "Access to localhost was denied" or HTTP 403:

### Solution 1: Use 127.0.0.1 instead of localhost

Try accessing:
```
http://127.0.0.1:5001
```

Instead of:
```
http://localhost:5001
```

### Solution 2: Check if server is running

```bash
# Check if server is running
ps aux | grep web_app

# Or test the server
python3 test_server.py
```

### Solution 3: Clear browser cache

- Hard refresh: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows)
- Or try incognito/private mode

### Solution 4: Check firewall settings

On macOS:
- System Settings → Network → Firewall
- Make sure Python/Flask is allowed

### Solution 5: Try a different port

The app auto-detects ports 5000-5009. If 5001 doesn't work, try:
- Check what port the server actually started on (shown in terminal)
- Or manually set a port in `web_app.py`

## Server Not Starting

### Error: "Address already in use"

```bash
# Kill any process on the port
lsof -ti:5001 | xargs kill -9

# Or use a different port
FLASK_RUN_PORT=5002 python3 web_app.py
```

### Error: "ModuleNotFoundError: No module named 'flask'"

```bash
# Install Flask
pip3 install flask

# Or use venv
source venv/bin/activate
pip install flask
```

## Quick Test

Run this to test if server is accessible:

```bash
python3 test_server.py
```

This will test both `127.0.0.1` and `localhost` URLs.

## Still Having Issues?

1. **Check server logs**: Look at the terminal where you ran `python3 web_app.py`
2. **Try curl**: `curl http://127.0.0.1:5001/health`
3. **Check browser console**: Open Developer Tools (F12) and check for errors
4. **Try different browser**: Chrome, Firefox, Safari

