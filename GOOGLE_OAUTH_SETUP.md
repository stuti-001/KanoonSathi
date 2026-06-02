# Google OAuth Setup Guide

## Overview

The KanoonSathi application now supports Google OAuth login and signup. This guide will help you set up Google OAuth credentials.

## Prerequisites

- Google Cloud Console access
- Admin access to your project

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project selector at the top and click "NEW PROJECT"
3. Enter "KanoonSathi" as the project name
4. Click "CREATE"

## Step 2: Enable Google Identity Services API

1. In the Google Cloud Console, search for "Google Identity Services API"
2. Click on it and click "ENABLE"

## Step 3: Create OAuth 2.0 Credentials

1. Go to "Credentials" in the left sidebar
2. Click "CREATE CREDENTIALS" → "OAuth client ID"
3. If prompted, configure the OAuth consent screen first:
   - Choose "External" for User Type
   - Fill in the required information:
     - App name: "KanoonSathi"
     - User support email: Your email
     - Developer contact: Your email
   - Add these scopes: `userinfo.email`, `userinfo.profile`
   - Add yourself as a test user
4. Return to create credentials → OAuth client ID
5. Select "Web application"
6. Add Authorized JavaScript Origins:
   - `http://localhost:8000`
   - `http://localhost`
   - `http://127.0.0.1:8000`
   - Your production domain (when deployed)
7. Add Authorized redirect URIs:
   - `http://localhost:8000/`
   - `http://localhost:8000/login/`
   - `http://localhost:8000/signup/`
   - Your production URLs (when deployed)
8. Click "CREATE"
9. Copy the **Client ID** (you'll need this)

## Step 4: Configure Environment Variables

1. Open the `.env` file in your project root (created at `c:\Users\ASUS\project\.env`)
2. Find the line with `GOOGLE_OAUTH_CLIENT_ID=YOUR_GOOGLE_OAUTH_CLIENT_ID_HERE`
3. Replace `YOUR_GOOGLE_OAUTH_CLIENT_ID_HERE` with your Client ID from Step 3
4. Save the file

Example:

```
GOOGLE_OAUTH_CLIENT_ID=123456789-abcdefghijklmnop.apps.googleusercontent.com
```

## Step 5: Install Required Python Package

If not already installed, install the Google authentication library:

```bash
pip install google-auth
```

## Step 6: Test the Setup

1. Start your Django development server:

   ```bash
   python manage.py runserver
   ```

2. Navigate to `http://localhost:8000/login/`
3. Click "Continue with Google"
4. You should see the Google Sign-In prompt
5. Follow the Google authentication flow

## How It Works

### Frontend Flow

1. User clicks "Continue with Google" button
2. Google Sign-In SDK displays the authentication dialog
3. User authenticates with their Google account
4. Google returns an ID token to the frontend

### Backend Flow

1. Frontend sends the ID token to `/api/auth/google`
2. Backend verifies the token using the Google Client ID
3. If valid, the backend:
   - Extracts user email and name from the token
   - Creates or updates the local user account
   - Logs the user in
   - Returns user info to the frontend

### Storage

- User information is stored in Django's User model
- Authentication state is stored in browser localStorage
- OAuth tokens are included for session management

## Troubleshooting

### Issue: "Google OAuth not configured"

- Check that `GOOGLE_OAUTH_CLIENT_ID` is set in `.env`
- Ensure the `.env` file is in the project root
- Restart the Django development server

### Issue: "Invalid token"

- Make sure the Client ID in `.env` matches the one from Google Cloud Console
- Check that authorized origins/redirect URIs are configured correctly
- Clear browser cache and try again

### Issue: CORS errors

- The backend has CSRF exemption for `/api/auth/google`, so CORS shouldn't be an issue
- Check browser console for specific error messages

## Production Deployment

Before deploying to production:

1. Create a new OAuth 2.0 Client ID for your production domain
2. Update `.env` with the new Client ID
3. Add your production domain to "Authorized JavaScript Origins" and "Authorized redirect URIs" in Google Cloud Console
4. Ensure `.env` is not committed to version control (add to `.gitignore`)
5. Use environment variables in your production deployment tool (Docker, Heroku, etc.)

## Security Notes

- Never commit `.env` file to version control
- Use different OAuth credentials for development and production
- Regularly audit connected applications in your Google Account settings
- Consider implementing additional user verification for lawyer accounts

## References

- [Google Sign-In for Web Documentation](https://developers.google.com/identity/gsi/web)
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Django Authentication Documentation](https://docs.djangoproject.com/en/6.0/topics/auth/)
