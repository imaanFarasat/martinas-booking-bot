# Combined Nail Booking System

## 🎯 Overview

This is now a **single, unified system** that runs both the admin bot and staff bot in one deployment. This solves the previous deployment issues and makes the system much more maintainable.

## 📁 Current Structure

```
booking-nail/
├── bot_async.py          # Main admin bot (management functions)
├── staff_bot.py          # Staff bot (schedule viewing)
├── web_server.py         # Flask server that runs both bots
├── database.py           # Shared database operations
├── config.py             # Shared configuration
├── requirements.txt      # Combined dependencies
├── render.yaml           # Single deployment configuration
├── shared_scheduler.db   # Shared database (both bots use this)
└── [other files...]
```

## 🚀 How It Works

1. **Single Web Service**: One Render service runs everything
2. **Shared Database**: Both bots access the same `shared_scheduler.db`
3. **Multi-threaded**: Each bot runs in its own thread
4. **Flask Server**: Provides health checks and monitoring

## 🔧 Environment Variables Needed

Set these in your Render dashboard:

| Variable | Purpose | Example |
|----------|---------|---------|
| `BOT_TOKEN` | Admin bot token from @BotFather | `1234567890:ABCdef...` |
| `STAFF_BOT_TOKEN` | Staff bot token from @BotFather | `9876543210:XYZabc...` |
| `ADMIN_IDS` | Comma-separated admin user IDs | `123456789,987654321` |
| `DATABASE_PATH` | Database file path | `/opt/render/project/src/shared_scheduler.db` |

## 📱 Bot Functions

### Admin Bot (`bot_async.py`)
- ✅ Schedule management
- ✅ Staff management  
- ✅ Booking management
- ✅ PDF generation
- ✅ Admin-only functions

### Staff Bot (`staff_bot.py`)
- ✅ View personal schedule
- ✅ Current week display
- ✅ Staff selection
- ✅ Read-only access

## 🎉 Benefits of Combined Setup

1. **Single Deployment**: Only one Render service to manage
2. **Shared Database**: No conflicts between bots
3. **Cost Effective**: One service instead of two
4. **Easier Maintenance**: One codebase to update
5. **Better Resource Management**: Shared dependencies

## 🚀 Deployment Steps

1. **Push to GitHub**: All files are now in one repository
2. **Create Render Service**: Use the `render.yaml` configuration
3. **Set Environment Variables**: Add the required tokens and IDs
4. **Deploy**: Render will build and start both bots automatically

## 🔍 Troubleshooting

### If bots don't start:
- Check environment variables are set correctly
- Verify bot tokens are valid
- Check Render logs for specific errors

### If database issues:
- Ensure `shared_scheduler.db` exists
- Check database permissions
- Verify table structure

## 📞 Support

Both bots will now run together in a single, stable deployment. The previous issues with separate deployments and database conflicts have been resolved.

---

**Status**: ✅ Ready for deployment
**Last Updated**: July 23, 2025 